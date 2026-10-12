# Project setup and execution

The [README](README.md) is the canonical setup, API contract, and testing guide. Use Node 24 and Python 3.12, install with `npm ci` and `uv sync --frozen`, and copy `.env.example` to `.env.local` before adding credentials.

Run the backend and frontend in separate terminals:

```sh
uv run --frozen python scripts/dev_server.py
npm run dev
```

The backend listens on `127.0.0.1:8000`, and Vite defaults to `http://localhost:5173`. Set `FRONTEND_URL` to the exact browser origin. If you explicitly use `npm run dev -- --port 3000`, set `FRONTEND_URL=http://localhost:3000`. Stop each server with Ctrl+C in its own terminal.

Required API settings are `FRONTEND_URL`, `GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, and `COLLECTION_NAME`. Use `COLLECTION_NAME=portfolio-live` for the stable corpus alias. Configure the same alias in deployment and ingestion.

Refresh documentation safely:

```sh
uv run --frozen python scripts/ingest.py --alias portfolio-live
uv run --frozen python scripts/check_qdrant.py
```

The script builds and verifies a versioned replacement before switching the alias. It retains the old collection and prints its rollback command. Existing physical collections such as `portfolio` are never deleted; see the README for first-time alias migration and rollback instructions.
