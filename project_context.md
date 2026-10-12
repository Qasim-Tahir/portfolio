# Portfolio implementation context

Current public content is defined in `content/portfolio.json`. React uses it directly, and `scripts/sync_content.py` generates indexed project/profile summaries. Run the synchronization check before ingestion. `content/claims.json` records the evidence status of historical claims; `reference/legacy-content/` retains the old narratives outside the corpus.

The visual design and mandatory terminal boot sequence are owner preferences. Preserve them.

## Runtime

React 18, Vite 8, Framer Motion and sanitized Markdown render the portfolio. The Python handler in `api/chat.py` exposes `/api/chat`; the local FastAPI bridge awaits the same async pipeline. Qdrant Cloud Inference uses `sentence-transformers/all-minilm-l6-v2`, named `content_vector`, 384 dimensions and cosine similarity. The default collection alias is `portfolio-live`; `COLLECTION_NAME` overrides it during a controlled migration. Generation and safeguard IDs live in `server/prompts.py`.

Requests have a cancellable 24-second application budget, eight-second provider timeouts and no Groq retries. Client cleanup has a separate one-second bound. Vercel is configured for 28 seconds and the browser for 30. Browser abort prevents stale UI updates but does not promise remote provider compute cancellation. No streaming is implemented.

Production requires shared atomic Redis quotas. Vercel supplies the trusted forwarded IP; direct development uses the socket address. Missing shared-store configuration fails closed. Pattern filters, strict safeguard verdicts and citation quote validation do not prove complete jailbreak resistance or semantic truth.

## Content and corpus refresh

Use the commands and environment instructions in README.md and project_setup.md. Build a replacement collection, verify it, then switch the alias atomically. Retain the previous physical collection for rollback. Do not delete the served collection. Old benchmark comparator versions and evaluation dates remain unknown; never relabel historical scores as new-model results.

## Checks

Node 24 and Python 3.12 are required. Run npm lint/test/build, frozen Python dependency installation, unit tests, content synchronization checks and the opt-in evaluation commands documented in README.md. Provider-free regressions do not establish live answer quality, cost or latency.
