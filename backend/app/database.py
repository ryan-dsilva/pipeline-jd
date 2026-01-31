from functools import lru_cache
from collections.abc import Mapping

from pocketbase import PocketBase

from app.config import settings


@lru_cache(maxsize=1)
def get_pb() -> PocketBase:
    """Lazy-init PocketBase client (fails only when actually called, not at import)."""
    return PocketBase(settings.POCKETBASE_URL)


# Module-level proxy for convenience. Accessing attributes will trigger init.
class _PBProxy:
    def __getattr__(self, name):
        return getattr(get_pb(), name)


pb: PocketBase = _PBProxy()  # type: ignore[assignment]


def sanitize_pb_value(value: str) -> str:
    """Escape special characters for use in PocketBase filter strings.

    PocketBase filter values are enclosed in single quotes, so we must escape
    backslashes first, then single quotes.
    """
    return value.replace("\\", "\\\\").replace("'", "\\'")


def record_to_dict(record) -> dict:
    """Convert a PocketBase record object to a plain dict.

    Handles three storage patterns:
    1. PB SDK records that store fields in an internal ``__data`` dict
    2. Objects that expose fields as public attributes (``__dict__``)
    3. Mapping-like objects (dict subclasses, etc.)

    System fields (id, created, updated, collection_id, collection_name) are
    always extracted via ``getattr`` so they are never missed.
    """
    data: dict = {}

    # 1. Try the PB SDK internal storage first (private ``__data`` dict).
    #    The SDK stores record fields in ``_Record__data`` (name-mangled).
    internal = getattr(record, "_Record__data", None) or getattr(record, "__data", None)
    if isinstance(internal, dict):
        data.update(internal)

    # 2. Merge public attributes from __dict__ (covers mock objects and simple
    #    attribute-based storage).
    if hasattr(record, "__dict__"):
        for k, v in record.__dict__.items():
            if not k.startswith("_"):
                data[k] = v

    # 3. Merge mapping-style fields last (covers dict subclasses).
    try:
        is_mapping = isinstance(record, Mapping)
    except Exception:
        is_mapping = False
    if is_mapping:
        for k, v in record.items():
            data[k] = v

    # 4. Always pull system fields via getattr to guarantee they are present.
    for key in ("id", "created", "updated", "collection_id", "collection_name"):
        val = getattr(record, key, None)
        if val is not None:
            data[key] = val

    return data


def upsert_section(job_id: str, section_key: str, data: dict) -> dict:
    """Upsert a section by (job, section_key). Returns the record as a dict."""
    from pocketbase.utils import ClientResponseError  # type: ignore[import-untyped]

    safe_job = sanitize_pb_value(job_id)
    safe_key = sanitize_pb_value(section_key)
    try:
        existing = pb.collection("sections").get_first_list_item(
            f"job = '{safe_job}' && section_key = '{safe_key}'"
        )
        record = pb.collection("sections").update(existing.id, data)
    except (ClientResponseError, Exception) as exc:
        # Only treat "not found" as a create trigger
        is_not_found = (
            isinstance(exc, ClientResponseError) and exc.status == 404
        ) or "not found" in str(exc).lower()
        if not is_not_found:
            raise
        # Record doesn't exist — create it
        data["job"] = job_id
        data["section_key"] = section_key
        record = pb.collection("sections").create(data)
    return record_to_dict(record)
