# Project Setup & Execution Guide

This project uses a dual-server architecture for local development to ensure high performance and stability for the RAG chatbot.

## 🚀 Running the Project

To start the full environment (Frontend + Backend), run these commands in separate terminals:

### Terminal 1: Backend (FastAPI + RAG Engine)
This server handles the Qdrant retrieval, Groq LLM inference, and the Safety Shield.
```bash
uv run scripts/dev_server.py
```

### Terminal 2: Frontend (Vite + React)
This serves the portfolio UI and proxies `/api` requests to the backend.
```bash
npm run dev -- --port 3000
```

---

## 🛑 Stopping the Servers

If you see an error like `[Errno 98] Address already in use`, it means the ports are still occupied by previous sessions. Use these commands to force-stop them:

### To stop EVERYTHING:
```bash
# Kills processes running on ports 3000 (Vite) and 8000 (FastAPI)
fuser -k 3000/tcp 8000/tcp
```

### Individual stop commands:
*   **Stop Frontend only**: `fuser -k 3000/tcp`
*   **Stop Backend only**: `fuser -k 8000/tcp`

---

## 🛠️ Maintenance & Ingestion

If you update your documentation in the `/docs` folder and need to refresh the AI's knowledge base:

```bash
# Re-ingest documents into Qdrant
uv run scripts/ingest.py
```

## 🔐 Environment Variables
Ensure your `.env.local` contains:
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `GROQ_API_KEY`
- `COLLECTION_NAME=portfolio`
