# Portfolio Project — Context & Decision Log

## Project Goal

Build and deploy a personal portfolio website for **Qasim Tahir** (AI/ML Engineer) that:

- Displays skills, education, and projects
- Embeds a **live RAG chatbot** that answers technical questions by querying actual project documentation
- Demonstrates RAG expertise directly — the chatbot _is_ the proof of skill

---

## Personal Info

**Name:** Qasim Tahir
**Role:** AI/ML Engineer (Aspiring)
**Education:** BS Data Science, FAST-NUCES — Sep 2021 to Present
**Aesthetic:** Glassmorphic Dark Mode with smooth scroll (ReactLenis)

**Professional Summary:** Strong fundamentals in LLMs, Generative AI, and NLP. Experienced in building Multi-Modal RAG pipelines and automation workflows.

---

## Projects

### 1. CogniSynth: GraphRAG + VLM Pipeline

**Period:** Jan 2026 — Present

- Multi-modal GraphRAG + VLM pipeline for deep structural and visual understanding of ML/AI research papers
- Dual NER strategy: GLiNER + Groq Llama 4 with canonical deduplication
- Entities extracted: Model, Dataset, Metric and their relational interactions
- HyDE for intent alignment, BGE-M3 cross-encoder reranking, LLM-based faithfulness verification
- Evaluation suite: Ragas + custom 4-axis LLM-as-a-Judge (Hit Rate, Faithfulness, Density, Structure)
- Stack: Docling, Neo4j, Groq

### 2. Lecture Notes Summarizer OCR (LuminaNotes)

**Period:** Sep 2025 — Mar 2026
**GitHub:** https://github.com/Qasim-Tahir/Lecture-Notes-Summarizer-OCR

- Converts PDFs, PPTX, images, and videos into structured Notion-ready markdown and exam-focused Q&A pairs
- Uses Groq (Llama 3 Vision) + Whisper
- Multi-stage text merging architecture and automated hallucination verification
- Specialized OCR sub-modules for LaTeX math notation, complex tables, slide screenshots
- Stack: pdf2image, Pillow, moviepy, libreoffice, poppler-utils

### 3. AI-Powered Invoice Processing & Automation

**Period:** 2026

- End-to-end n8n automation workflow processing emails with invoice attachments
- FastAPI service + Vision-Language Model for structured data extraction
- Validation layer with conditional logic; dedicated error-handling pipeline for invalid/ambiguous invoices
- Stack: n8n, FastAPI, VLM, Python

### 4. Islamic Source Finder

**Period:** 2024

- Python-based semantic retrieval of Quranic verses and Hadith references
- Multi-modal query pipeline: text, image, audio, video inputs
- OCR for image inputs, Whisper speech-to-text for audio
- Video pipeline: extracts audio from YouTube, Instagram, Facebook
- Stack: Python, RAG, OCR, Whisper

---

## Skills

| Category   | Technologies                                                             |
| ---------- | ------------------------------------------------------------------------ |
| AI/ML      | LangChain, LlamaIndex, LangGraph, HuggingFace, Neo4j, PyTorch, TensorFlow |
| Vector DBs | Qdrant, ChromaDB, FAISS, Pinecone                                        |
| Backend    | FastAPI, Flask, Node.js, Docker, Azure, PostgreSQL                        |
| Tools      | n8n, Groq, Git, Linux                                                    |

---

## Architecture Decision

### Chosen Stack: Vercel Serverless Python + Qdrant Cloud Inference

**Frontend:** React 18 (Vite 5) — deployed as static files on Vercel edge network
**Backend:** Python serverless function at `/api/chat.py` — Vercel `BaseHTTPRequestHandler`
**Vector DB:** Qdrant Cloud with `cloud_inference=True` — embedding handled server-side by Qdrant
**Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` via Qdrant Cloud Inference (384-dim). Both ingestion and query use `Document(text=..., model=EMBED_MODEL)` — no local embedding library needed at runtime.
**Inference:** Groq + `llama-3.1-8b-instant` — sub-second responses
**Smooth Scroll:** `@studio-freight/react-lenis` wrapping the entire app (`lerp: 0.1`, `wheelMultiplier: 1.2`)

**Why this stack:**

- Frontend and `/api` share the same domain → zero CORS config in production
- Vercel serverless cold start: 1–2 seconds vs Render container: 30+ seconds
- One repo, one deploy, one free-tier service
- Python backend stays within Vercel's 10-second function timeout (RAG chain runs in 2–4 seconds)
- Qdrant Cloud Inference eliminates the need for `fastembed` or `sentence-transformers` in the serverless bundle — stays well under Vercel's 250MB limit

---

## Folder Structure

```
web/
│
├── .env.local                    # Local environment variables (never committed)
├── .gitignore                    # Git ignore file
├── .python-version               # Python version constraint spec file
├── .vercelignore                 # Instructs Vercel what files to exclude from deployment
├── index.html                    # Entrypoint HTML — loads Google Fonts (Inter, Outfit)
├── main.py                       # Python template file (unused)
├── package.json                  # NPM packages & scripts
├── package-lock.json             # NPM package lockfile
├── project_context.md            # Portfolio Project context and log (this file)
├── project_setup.md              # Project local development setup guide
├── pyproject.toml                # UV/Python dependency specifications
├── security_tests.sh             # Bash script to run security validation tests
├── uv.lock                       # UV lockfile
├── vercel.json                   # Vercel configuration (build rules, rewrites, security headers)
├── vite.config.js                # Vite config with /api proxy to localhost:8000
│
├── api/                          # Vercel Serverless Backend Functions
│   └── chat.py                   # RAG Endpoint: validates, rate-limits, filters injections,
│                                 #   runs safety shield, embeds via Qdrant Cloud Inference,
│                                 #   retrieves context, calls Groq, sanitizes output
│
├── docs/                         # RAG Knowledge Base markdown source docs (10 files)
│   ├── about.md                  # Qasim Tahir biographical detail and skills summary
│   ├── cognisynth-technical.md   # Deep technical details on CogniSynth GraphRAG
│   ├── cognisynth.md             # Overview of the CogniSynth GraphRAG project
│   ├── invoice-automation.md     # Details of the AI Invoice Automation system
│   ├── islamic-source-finder-technical.md # Technical doc on Islamic Source Finder
│   ├── islamic-source-finder.md  # Overview of the Islamic Source Finder
│   ├── ocr-summarizer-technical.md # Deep technical details on the OCR Summarizer (LuminaNotes)
│   ├── ocr-summarizer.md         # Overview of the Lecture Notes Summarizer OCR
│   ├── portfolio-rag-technical.md # Technical doc on this portfolio RAG pipeline itself
│   └── portfolio-rag.md          # Overview of the portfolio RAG project
│
├── knowledge_base/               # (Empty) Reserved directory for future use
│
├── scripts/                      # Local maintenance and utility scripts (never deployed)
│   ├── check_qdrant.py           # Inspect Qdrant Cloud collection status (points count, vector size)
│   ├── dev_server.py             # FastAPI bridge wrapping chat.py's BaseHTTPRequestHandler for local dev
│   └── ingest.py                 # local ingestion: Chunk → Embed (Cloud Inference) → Upsert to Qdrant
│
├── src/                          # Vite + React Frontend Application
│   ├── App.jsx                   # Root layout: ReactLenis smooth scroll → AnimatePresence →
│   │                             #   TerminalBoot (intro) → main content sections
│   ├── index.css                 # Custom glassmorphic dark-mode stylesheet with CSS variables,
│   │                             #   responsive breakpoints, and smooth scroll (html { scroll-behavior: smooth })
│   ├── main.jsx                  # React 18 entrypoint (StrictMode → App)
│   └── components/
│       ├── About.jsx             # Two-card grid: bio + philosophy with education badges
│       ├── ChatBot.jsx           # RAG ChatBot widget with tooltip peek, click-outside dismiss,
│       │                         #   pulse animation, ReactMarkdown rendering, source badges
│       ├── Contact.jsx           # Contact section with email obfuscation, social links, footer
│       ├── Hero.jsx              # Centered hero with word-reveal animation, ambient gradient orbs,
│       │                         #   resume download button, CTA buttons
│       ├── Nav.jsx               # Fixed navbar with smooth-scroll anchors, mobile hamburger drawer
│       ├── Projects.jsx          # Project cards grid with data-flow pipeline visualization,
│       │                         #   tech pills, GitHub/demo links
│       ├── Skills.jsx            # Four-category skill grid (AI/ML, Vector DBs, Backend, Tools)
│       └── TerminalBoot.jsx      # Animated Python-style boot sequence intro screen (4s duration)
│
└── public/                       # Static assets (currently empty; resume.pdf expected here)
```

---

## NPM Dependencies

```json
{
  "dependencies": {
    "@studio-freight/react-lenis": "^0.0.47",
    "framer-motion": "^11.2.10",
    "lucide-react": "^0.395.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^10.1.0",
    "rehype-sanitize": "^6.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.3.1",
    "eslint": "^8.57.0"
  }
}
```

---

## Environment Variables

```
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_key
GROQ_API_KEY=your_key
FRONTEND_URL=https://your-domain.vercel.app   # or http://localhost:3000 for local
COLLECTION_NAME=portfolio-rag
```

Set in `.env.local` locally. Set in Vercel dashboard under Project → Settings → Environment Variables for production.

---

## Key Files

### `pyproject.toml` (Unified Python Project Configuration)

```toml
[project]
name = "web"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.136.1",
    "groq>=1.2.0",
    "langchain-text-splitters>=1.1.2",
    "python-dotenv>=1.2.2",
    "qdrant-client>=1.18.0",
    "uvicorn>=0.47.0",
]
```

### `vercel.json` (Vercel Build Routing, Rewrites & Security Headers)

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/chat", "destination": "/api/chat.py" },
    { "source": "/((?!assets/).*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### `vite.config.js` (Dev Proxy Configuration)

```js
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
```

---

## Ingestion Logic (`scripts/ingest.py`)

- Loads all `.md` files from `docs/` (currently 10 files)
- Splits using `MarkdownHeaderTextSplitter` (by `##` and `###`) then `RecursiveCharacterTextSplitter` (chunk size 500, overlap 80)
- Embeds using Qdrant Cloud Inference: `Document(text=chunk, model="sentence-transformers/all-minilm-l6-v2")` — no local embedding model needed
- Creates collection with named vector `content_vector` (384-dim, cosine distance)
- Upserts to Qdrant Cloud in batches of 50
- Payload per chunk: `text`, `source`, `section`, `subsection`
- Skips chunks under 50 characters
- Deletes and recreates collection on each run (clean slate)
- Run once locally. Re-run only when docs are updated.

---

## RAG Endpoint Logic (`api/chat.py`)

### Security Pipeline (4 Layers)

1. **Input Validation** — Content-Type check, body size cap (32KB), message count cap (20), message length cap (2000 chars), role whitelist (`user`/`assistant`)
2. **Rate Limiting** — In-memory per-IP rate limiter (10 requests per 60-second window)
3. **Layer 1: Deterministic Injection Block** — Regex patterns against normalized text (handles homoglyphs, zero-width chars, spaced-out letters). Blocks before any model call.
4. **Layer 2: Model-based Safety Shield** — `gpt-oss-safeguard-20b` via Groq classifies the query. Fails closed on error.
5. **Layer 3: Persona-Hardened Model Call** — System prompt with strict identity rules and security rules that cannot be overridden.
6. **Layer 4: Output Sanitization** — Regex scan of model output for forbidden patterns (env var names, API key patterns, internal collection names, system prompt fragments).

### RAG Flow

1. Receive POST with `{ messages: [...] }` (full chat history)
2. Embed the latest user message using Qdrant Cloud Inference (`Document` with `sentence-transformers/all-minilm-l6-v2`)
3. Query Qdrant for top-5 chunks by cosine similarity (named vector: `content_vector`)
4. Construct system prompt with retrieved context injected
5. Call Groq (`llama-3.1-8b-instant`, max 512 tokens, temp 0.3)
6. Sanitize reply → Return `{ reply: string, sources: string[] }`

### CORS

- `Access-Control-Allow-Origin` is set to `FRONTEND_URL` env var (both local and production)
- CORS is handled directly in `chat.py`'s `BaseHTTPRequestHandler`, not via middleware
- The dev server (`dev_server.py`) bridges requests to the same handler, ensuring identical behavior

---

## Frontend Architecture

### App Component (`App.jsx`)

The root component wraps the entire application in `ReactLenis` for smooth scroll, then uses `AnimatePresence` for a boot → main transition:

1. **TerminalBoot** — 4-second animated Python-style boot sequence (`from portfolio.agent import RAG_Assistant`)
2. **Main App** — Fades in after boot completes, rendering all sections in order:
   `Nav → Hero → About → Skills → Projects → ChatBot → Contact`

### Component Details

| Component       | Key Features                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------- |
| `TerminalBoot`  | Fira Code monospace, staggered clip-path reveal, blinking cursor, 4s auto-complete                  |
| `Nav`           | Fixed position, backdrop blur, scroll detection for border, smooth-scroll anchor links, mobile drawer |
| `Hero`          | Word-by-word reveal animation, ambient gradient orbs, resume download button, centered layout        |
| `About`         | Two-card responsive grid (bio + philosophy), education badges (BS DS / FAST)                         |
| `Skills`        | 4 categories: AI/ML, Vector DBs, Backend, Tools. Uses `tech-pill` CSS class                          |
| `Projects`      | 4 project cards with data-flow pipeline visualization (3-step arrows), tech pills, action links      |
| `ChatBot`       | Fixed-position widget, pulse animation CTA, delayed tooltip peek, click-outside dismiss, ReactMarkdown with rehype-sanitize, typing indicator, source badges |
| `Contact`       | Email obfuscation (JS concatenation), GitHub/LinkedIn social links, MapPin location, footer           |

### CSS Design System (`index.css`)

- `html { scroll-behavior: smooth }` for native smooth scroll fallback
- CSS Variables: `--bg: #121212`, `--accent: #3b82f6`, `--glass`, `--glass-border`, `--text-dim: #cbd5e1`
- Typography: Inter (body), Outfit (headings), 800 weight for display
- Body background: radial gradient glow + 40px grid lines
- Glassmorphic cards with hover lift (`translateY(-8px) scale(1.01)`) and light-sweep `::before`
- Responsive: mobile breakpoint at 768px (reduced padding, hidden nav links, full-width chat)

---

## Chatbot UX Design

**Widget name:** "Project RAG Engine"
**Subtitle:** "Qdrant · Groq · Llama 3.1"

**CTA Button:** "Ask AI Agent" with Sparkles icon and pulse-ring animation (3s infinite)
**Delayed Tooltip:** Appears after 5 seconds if chat not opened: "I'm a live RAG pipeline. Ask me how Qasim's architecture works."

**Welcome message:** "Hi! I'm a live RAG pipeline running on Qdrant + Groq, querying Qasim's actual project documentation. Ask me anything technical about his work."

**Starter prompts (technical):**

- "How is the knowledge graph built in CogniSynth?"
- "How did you handle hallucinations in the OCR project?"
- "Explain the error handling in the Invoice Automation."
- "What vision models are used in the OCR summarizer?"

**Show retrieved sources** below each bot response as badges.
**Click-outside dismiss** — clicking outside the chat window closes it.

---

## Local Development

Run two terminals simultaneously:

```bash
# Terminal 1: Python API server (FastAPI bridge)
uv run scripts/dev_server.py

# Terminal 2: Vite frontend dev server with API proxy
npm run dev -- --port 3000
```

Vite proxies `/api/*` requests to `http://127.0.0.1:8000` (configured in `vite.config.js`).

---

## Docs Structure (per project markdown file)

Each file in `docs/` should follow this template:

```
# Project Name
## Overview
## Problem Statement
## Architecture
## Key Technical Decisions
## Implementation Details
## Challenges & Solutions
## Tech Stack
## Results & Outcomes
## FAQ
```

The FAQ section is the highest-leverage part — write explicit Q&A for every question a technical recruiter or senior engineer might ask. RAG retrieves only what is written.

---

## Accounts Needed

| Service      | Purpose                                 | Cost       |
| ------------ | --------------------------------------- | ---------- |
| Vercel       | Frontend + serverless functions hosting | Free       |
| Qdrant Cloud | Managed vector database + inference     | Free (1GB) |
| Groq Cloud   | LLM inference + safety shield           | Free tier  |
| GitHub       | Version control                         | Free       |

## Security Status & Hardening

| Feature                    | Implementation                                        | Status |
| -------------------------- | ----------------------------------------------------- | ------ |
| **Input Validation**       | Strict size/type/role checks in `api/chat.py`         | ✅     |
| **Rate Limiting**          | In-memory per-IP (10 req / 60s window)                | ✅     |
| **Injection Detection**    | Regex patterns + unicode normalization + homoglyph map | ✅     |
| **Error Handling**         | Sanitized responses (no tracebacks leaked)             | ✅     |
| **CORS Policy**            | Locked to `FRONTEND_URL` env var                       | ✅     |
| **Security Headers**       | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` via `vercel.json` | ✅     |
| **Deployment Security**    | `.vercelignore` excludes scripts, docs, env files, context docs | ✅     |
| **Identity Protection**    | Strict system prompt boundaries (never reveal config)  | ✅     |
| **Safety Shield**          | `gpt-oss-safeguard-20b` classifier (fails closed)     | ✅     |
| **Output Sanitization**    | Regex scan for forbidden patterns (keys, env vars, internal names) | ✅     |
| **Email Obfuscation**      | JS concatenation in Contact.jsx (no mailto in HTML)    | ✅     |

## Environment Variable Registry

| Key               | Purpose                  | Required In        |
| ----------------- | ------------------------ | ------------------ |
| `QDRANT_URL`      | Vector DB Cluster URL    | Local & Production |
| `QDRANT_API_KEY`  | Vector DB API Key        | Local & Production |
| `GROQ_API_KEY`    | LLM API Key              | Local & Production |
| `FRONTEND_URL`    | Allowed CORS Origin      | Local & Production |
| `COLLECTION_NAME` | Target Vector Collection | Local & Production |

### Historical Bug & Vector Alignment Log:

**Issue:** Vector Name Mismatch (`using="content_vector"`)
- **Context:** In early iterations, query endpoints would fail with a `Not existing vector name error: content_vector` if the ingestion pipeline didn't name the vector explicitly or if it was omitted.
- **Resolution/Alignment:** The pipeline was unified. `scripts/ingest.py` explicitly creates the collection with a named vector parameter `content_vector` (384-dim, cosine) and upserts under this key using Qdrant Cloud Inference `Document` objects. In turn, `api/chat.py` queries Qdrant with `using="content_vector"` and also uses `Document` objects for embedding. Both files are fully aligned on using this named vector config.
- **Verification:** Local FastAPI server and `security_tests.sh` pass cleanly showing that the RAG retrieval endpoint resolves and queries successfully.
