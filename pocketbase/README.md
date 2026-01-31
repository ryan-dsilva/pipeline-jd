# PocketBase

## Migrations
This project uses PocketBase migrations as the source of truth for the schema.

### Apply migrations on a fresh setup
1. Download the PocketBase binary for your platform (or use the existing `pocketbase/pocketbase`).
2. Run PocketBase with the migrations directory in this repo:

```bash
cd pocketbase
./pocketbase serve
```

On first run, PocketBase will create a new `pb_data/` and apply migrations from `pb_migrations/`.

### Notes
- `pb_data/` is intentionally **not** committed (local data only).
- `pb_migrations/` **is** committed and should be used to recreate schema.
