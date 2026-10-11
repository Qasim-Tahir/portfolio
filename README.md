# Qasim Tahir portfolio

React and Vite render the portfolio. The Python `/api/chat` handler classifies the conversation with Groq, retrieves project documentation from Qdrant Cloud Inference, and generates an answer with Groq. `scripts/dev_server.py` adapts the same handler to FastAPI for local development. The existing visual design and terminal boot sequence are intentional.

## Setup

Use Node 24 and Python 3.12. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
npm ci
uv sync --frozen
cp .env.example .env.local
```

Fill in the Groq and Qdrant credentials in `.env.local`. `FRONTEND_URL` is required at API import and must match the browser origin. Vite defaults to `http://localhost:5173`. `COLLECTION_NAME` must identify the same corpus alias in local development, deployment, and ingestion. Never put secrets in frontend `VITE_*` variables or Markdown documents.

Run these in two terminals:

```sh
uv run --frozen python scripts/dev_server.py
npm run dev
```

Vite proxies `/api` to `127.0.0.1:8000`. Production uses the Python handler through `vercel.json`. Configure the same environment variables in Vercel, with the deployed frontend origin. `requirements.txt` contains only locked runtime dependencies; `requirements-dev.txt` also includes the local server and ingestion tools. `uv.lock` is the canonical resolution. Do not deploy `.env.local`.

## Safe corpus refresh

The script reads and validates every document before remote mutation. It uploads a new version collection, waits for writes, checks the exact count and named vector configuration, performs a retrieval smoke check, then switches the stable alias in one alias-update operation. The old collection stays available for rollback. Failed staging collections are retained for inspection and can be removed manually after confirming they are not served.

```sh
uv run --frozen python scripts/ingest.py --alias portfolio-live
uv run --frozen python scripts/check_qdrant.py
```

For an existing deployment whose `COLLECTION_NAME` is a physical collection such as `portfolio`, first ingest with a new alias such as `portfolio-live`. After successful verification, set `COLLECTION_NAME=portfolio-live` in the API environment. The script refuses to replace a physical collection with an alias of the same name and never deletes that collection. Keep the original environment setting available for rollback during this first migration.

Subsequent refreshes print the previous collection and a rollback command:

```sh
uv run --frozen python scripts/ingest.py --alias portfolio-live --rollback-to PREVIOUS_COLLECTION
```

`check_qdrant.py` checks the exact count, the 384-dimensional cosine `content_vector`, the alias target, and embedding metadata from a sampled point. Legacy collections without embedding metadata are reported as unknown. The smoke check proves retrieval availability, not answer quality. Live corpus/model verification and a RAG evaluation set are separate backlog tasks.

## Chat contract and limits

Send an object with `messages`, containing complete alternating user/assistant turns and a final user question. A single user question is valid. Extra message fields are discarded. Limits are 32,768 UTF-8 body bytes, 20 messages, 2,000 characters per user message, and 6,000 per assistant message. The browser sends up to nine prior complete turns and trims further to fit the byte limit. Its visible transcript is retained; greetings, failures, and cancellation notices are excluded from API history. New chat resets history.

A successful response contains `reply` and a string array `sources`. Policy refusals return 200 with no sources. Invalid requests return 400 or 415; oversized bodies return 413; rate exhaustion returns 429 with `Retry-After`; provider failures return 503; timeouts return 504. CORS controls browser access to responses and is not API authentication.

The provider pipeline has a 24-second budget with an eight-second timeout per provider call and no Groq retries. The browser has a 30-second deadline and cancels on close, reset, or unmount. Browser cancellation does not guarantee termination of a request already running on the server. The local adapter runs synchronous providers in a worker thread and bounds streamed data before buffering.

The safeguard receives an explicit classification policy and must return a complete JSON verdict with an integer `violation` of 0 or 1. All other verdicts fail closed with a service error. Deterministic injection and output checks are heuristics. Public architecture and stack names are allowed; credentials, private deployment endpoints, and internal instructions are confidential. Keep confidential material out of the corpus. The current in-process rate guard does not enforce a shared quota across Vercel instances; shared limiting remains FYP-70.

## Checks

```sh
npm run lint
npm test
npm run build
uv run --frozen python -m unittest discover -s tests -v
bash security_tests.sh
```

The Python tests use mocked providers, isolate quota state, and assert status, response shape, refusal behavior, staging failures, and rollback. JavaScript tests cover at least 12 turns with an intervening failure, byte limits, errors, cancellation, timeout, and reset. No test command above calls paid providers or mutates a remote collection. Repeatable rendering and keyboard checks are documented in [tests/BROWSER_CHECKS.md](tests/BROWSER_CHECKS.md). The shell security entry point runs the deterministic API suite and exits nonzero on failure. These checks do not prove resistance to live model jailbreaks.

GitHub Actions runs lint, JavaScript tests, build, and Python tests on pushes and pull requests. Live deployment checks and provider-backed security/quality evaluation remain separate from this offline suite.

After changing Python dependencies, regenerate the lock and both manifests:

```sh
uv lock
uv export --frozen --no-dev --no-emit-project --no-hashes --output-file requirements.txt
uv export --frozen --no-emit-project --no-hashes --output-file requirements-dev.txt
```
