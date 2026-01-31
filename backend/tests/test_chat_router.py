"""Tests for chat router."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import _make_job_record, _make_section_record


def test_chat_job_not_found(client, mock_pb):
    """POST /api/chat/{job_id} returns 404 for missing job."""
    mock_pb.collection().get_one.side_effect = Exception("Not found")

    response = client.post(
        "/api/chat/nonexistent",
        json={"message": "Hello", "history": []},
    )
    assert response.status_code == 404


def test_chat_returns_sse_stream(client, mock_pb):
    """POST /api/chat/{job_id} returns SSE stream."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().get_full_list.return_value = [
        _make_section_record(content_md="Analysis content here"),
    ]

    # Mock AsyncAnthropic
    mock_stream_ctx = AsyncMock()
    mock_stream = AsyncMock()
    mock_stream.text_stream = AsyncMock()
    mock_stream.text_stream.__aiter__.return_value = iter(["Hello", " world"])
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_async_client = MagicMock()
    mock_async_client.messages.stream.return_value = mock_stream_ctx

    with patch("app.routers.chat.anthropic") as mock_anthropic:
        mock_anthropic.AsyncAnthropic.return_value = mock_async_client
        response = client.post(
            "/api/chat/test_job_id",
            json={"message": "Tell me about this role", "history": []},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_chat_passes_history(client, mock_pb):
    """POST /api/chat/{job_id} passes message history to Claude."""
    mock_pb.collection().get_one.return_value = _make_job_record()
    mock_pb.collection().get_full_list.return_value = []

    mock_stream_ctx = AsyncMock()
    mock_stream = AsyncMock()
    mock_stream.text_stream = AsyncMock()
    mock_stream.text_stream.__aiter__.return_value = iter(["OK"])
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_async_client = MagicMock()
    mock_async_client.messages.stream.return_value = mock_stream_ctx

    with patch("app.routers.chat.anthropic") as mock_anthropic:
        mock_anthropic.AsyncAnthropic.return_value = mock_async_client
        response = client.post(
            "/api/chat/test_job_id",
            json={
                "message": "Follow up",
                "history": [
                    {"role": "user", "content": "First message"},
                    {"role": "assistant", "content": "First response"},
                ],
            },
        )

    assert response.status_code == 200
    # Verify messages were built correctly
    call_kwargs = mock_async_client.messages.stream.call_args[1]
    messages = call_kwargs["messages"]
    assert len(messages) == 3  # 2 history + 1 new
    assert messages[-1]["content"] == "Follow up"
