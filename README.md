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

`check_qdrant.py` checks the exact count, the 384-dimensional cosine `content_vector`, the alias target, and embedding metadata from a sampled point. Legacy collections without embedding metadata are reported as unknown. The smoke check proves retrieval availability, not answer quality. The versioned evaluation runner is described below; corpus upload and live evaluation require explicit authorization for the prepared payload and providers.

## Chat contract and limits

Send an object with `messages`, containing complete alternating user/assistant turns and a final user question. A single user question is valid. Extra message fields are discarded. Limits are 32,768 UTF-8 body bytes, 20 messages, 2,000 characters per user message, and 6,000 per assistant message. The browser sends up to nine prior complete turns and trims further to fit the byte limit. Its visible transcript is retained; greetings, failures, and cancellation notices are excluded from API history. New chat resets history.

A successful response contains `reply`, a string array `sources`, and an optional `citations` array. New grounded answers return citations with `label`, `chunk_id`, `source`, `project`, `section`, `subsection`, `document_version`, `score`, and `excerpt`. The visible [S1] labels match expandable source passages. Quotes are plain text, not executable HTML. Only selected sources are listed, in retrieval order. Legacy replies remain readable with a label explaining that passages are unavailable. Policy refusals return 200 with no sources. Invalid requests return 400 or 415; oversized bodies return 413; rate exhaustion returns 429 with `Retry-After`; provider failures return 503; timeouts return 504. CORS controls browser access to responses and is not API authentication.

Vercel is configured with a 28-second platform maximum for `api/chat.py` ([duration configuration](https://vercel.com/docs/functions/configuring-functions/duration)). The async request pipeline uses a cancellable 24-second wall-clock budget around quota acquisition, classification, retrieval and generation. Eight-second provider network timeouts and zero Groq retries supplement that budget. Request clients belong to one event loop and close on cancellation, with a separate one-second cleanup bound. Slow socket body reads check the same deadline between underlying reads; the local ASGI adapter includes streamed buffering in its budget and awaits the pipeline directly. Tests cancel stalled calls at every provider stage and during quota acquisition. Browser requests have a 30-second deadline and cancel on close, reset, or unmount. Browser abort does not guarantee that a remote provider stops computing. The deployed platform cap still requires rollout verification. No streaming is implemented.

The safeguard receives an explicit classification policy and must return a complete JSON verdict with an integer `violation` of 0 or 1. All other verdicts fail closed with a service error. Deterministic injection and output checks are heuristics. Public architecture and stack names are allowed; credentials, private deployment endpoints, and internal instructions are confidential. Keep confidential material out of the corpus. Vercel requires the atomic shared limiter described below. Local development without shared-store credentials uses a process-only guard.

## Follow-ups and evidence

Retrieval keeps the current question and bounded context from up to nine earlier user questions. An explicitly named project starts a new retrieval topic. Otherwise the latest named project (or multiple names for an ambiguous comparison) and the preceding question help resolve follow-ups. Assistant messages never choose the retrieval topic; they can contain fabricated facts. The query is capped at 2,800 characters. No additional rewrite-model call, hybrid search, reranker, or universal score cutoff is introduced.

Each retrieved passage carries its project/section, stable point ID, document hash when available, and similarity score. Newly ingested chunks include explicit project metadata; legacy points derive a project from the source filename and report missing versions as unavailable. The generator requests [Groq strict structured outputs](https://console.groq.com/docs/structured-outputs), with a 768-token generation output cap to allow brief answers and verbatim quotes. It must select supporting passage labels and quote 20–600 characters exactly from each passage. The server formats absent inline tags from validated evidence and expands strict grouped references; existing tags must match the selected labels. The server rejects malformed, truncated, unknown, duplicate, mismatched, or fabricated references with 503. The browser validates the public citation shape before committing history.

Empty retrieval returns a defined no-documentation answer without running generation. When retrieved passages do not answer the question, the generation schema requires an explicit unsupported verdict with no answer claims or citations; the server returns the same no-documentation answer. Safe greetings and thanks return predefined social replies without fabricated sources, after conversation classification. Policy refusals have no citations.

These checks establish passage identity and quote provenance. They do **not** verify that the quoted text entails every answer claim, establish factual truth, or demonstrate live answer quality. Similarity is not answer confidence. Provider-backed answerability/abstention evaluation and any score-threshold decision remain FYP-84/FYP-96 until an authorized live run completes. Measure a held-out set before adding hybrid retrieval or reranking. Offline regressions cover topic switches, ambiguous follow-ups, metadata, exact-quote validation, abstention, and UI contract failures. To opt into a single Groq schema smoke check using a public fixture, run `uv run --frozen python scripts/check_generation_contract.py --live --output /tmp/portfolio-contract-result.json`. Without `--live` the command skips the provider request. It never queries Qdrant, records only model/configuration, token counts when returned, status and error class, and excludes credentials, provider URLs, and exception bodies. This compatibility check is not an end-to-end retrieval or answer-quality evaluation.

## Portfolio links and sharing

Project cards link to the verified public repositories for LuminaNotes, Islamic Source Finder, and this portfolio. Destinations not supplied or published here are explicitly unavailable; no evidence action uses a placeholder fragment. The portfolio engine demo opens the chat panel. Names identify the project for keyboard and assistive-technology users.

The favicon is `public/favicon.svg`. `public/social-preview.svg` is the editable source of the 1,200×630 PNG share card. Regenerate the PNG with `uv run --no-project --with cairosvg python -c 'import cairosvg; cairosvg.svg2png(url="public/social-preview.svg", write_to="public/social-preview.png")'`. Canonical and social URLs point to the verified public `https://qasim-tahir.vercel.app/` site. Static assets and API paths are excluded from the SPA fallback rewrite.

Head metadata is available without JavaScript, and a noscript fallback links to public projects. Full static prerendering was considered but is deferred: it would need to preserve the deliberate terminal boot and hydrate the existing motion components without mismatches. The normal presentation and boot timing remain unchanged.

## Shared rate limiting

Before deploying this branch, set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in Vercel. Use the HTTPS REST endpoint and a token with permission to run EVAL, TIME, sorted-set commands, PEXPIRE, and ZREM. Never use frontend `VITE_*` variables for these credentials. Missing configuration or a store outage returns 503 before model calls; production does not fall back to an independent process counter. This deployment requirement prevents the old cross-instance quota bypass.

One [Redis Lua operation](https://upstash.com/docs/redis/features/restapi) atomically removes expired entries, checks sliding-window quotas and active leases, and reserves all three together. Defaults are 10 accepted requests per IP in any 60 seconds, 60 accepted requests globally per 60 seconds, and 8 concurrent requests. `CHAT_GLOBAL_RATE_LIMIT` and `CHAT_MAX_CONCURRENT` configure the global caps. A lease expires after 32 seconds if a worker dies; normal completion, refusal, and failure release it sooner. Per-IP and global keys expire after 60 seconds of inactivity. No request retry is used for a lost Redis response because it may already have reserved quota. HTTP 429 includes the computed `Retry-After` in seconds.

Use a shared `CHAT_RATE_NAMESPACE` across instances serving one deployment and separate namespaces for preview and production. Keys hash the normalized IP and use a common Redis cluster hash tag. Vercel's ingress-overwritten `x-forwarded-for` identifies visitors only when the server environment has `VERCEL=1`; direct/local requests use the socket address. Configure an appropriate trusted boundary before deploying this handler behind another proxy. The quota limits accepted requests rather than providing authentication or an exact monetary budget.

The offline tests execute the actual Lua script in a shared Redis emulator across concurrent worker clients, test fresh-client quota continuity, TTL and lease expiry, global quotas, untrusted direct headers, 429 headers, and failure handling. They do not prove the hosted database's permissions, region latency, consistency settings, or the deployed platform duration; validate these in FYP-70/FYP-97 before treating the rollout as complete.

## Checks

```sh
npm run lint
npm test
npm run build
uv run --frozen python -m unittest discover -s tests -v
bash security_tests.sh
```

The Python tests use mocked providers, isolate quota state, and assert status, response shape, refusal behavior, staging failures, and rollback. JavaScript tests cover at least 12 turns with an intervening failure, byte limits, errors, cancellation, timeout, and reset. No test command above calls providers or mutates a remote collection. Repeatable rendering and keyboard checks are documented in [tests/BROWSER_CHECKS.md](tests/BROWSER_CHECKS.md). The shell security entry point runs the deterministic API suite and exits nonzero on failure. These checks do not prove resistance to live model jailbreaks.

GitHub Actions runs lint, JavaScript tests, build, and Python tests on pushes and pull requests. Live deployment checks and provider-backed security/quality evaluation remain separate from this offline suite.

After changing Python dependencies, regenerate the lock and both manifests:

```sh
uv lock
uv export --frozen --no-dev --no-emit-project --no-hashes --output-file requirements.txt
uv export --frozen --no-emit-project --no-hashes --output-file requirements-dev.txt
```


## Canonical public content

`content/portfolio.json` supplies project cards and work highlights directly to React. `scripts/sync_content.py` generates the matching indexed summaries, including the current TST role. Technical notes remain scoped descriptions. Run `python scripts/sync_content.py --check` before ingestion; CI rejects stale summaries. The default collection alias is `portfolio-live` in `server/config.py`, `.env.example`, examples and the illustrative terminal boot. Explicit environment overrides can select another compatible alias. Scoped retrieval requires the `project` keyword index and project metadata. The retained legacy physical `portfolio` collection is an inspection/archive source; rebuild it through the safe refresh process before serving it with the current API. Rollback rejects targets lacking the required model metadata or project index.

`content/claims.json` classifies historical claims against supplied artifacts. Public numerical promises without reproducible evidence were removed, including unversioned comparator rankings, accuracy guarantees and employer counts. The original narratives remain in `reference/legacy-content/` for traceability and are excluded from ingestion/deployment. Missing evidence does not establish that those numbers were false. LuminaNotes' configured Scout model is verified at a named public source revision. Employer responsibilities retain their original attribution and are labeled owner-reported in the corpus.

## Versioned evaluation

`evals/v1/tuning.jsonl` has six tuning cases. `heldout.jsonl` has twenty separate cases for facts, follow-ups, unknown answers, unrelated requests, attacks and social replies. Keep held-out cases unchanged while tuning prompts or thresholds; make a new dataset version for later changes. The v1 live baseline is preserved, and its failures are development evidence for v2. Fresh v2 questions were reserved before scope/retrieval remediation; the concepts overlap, so this is not an independent generalization benchmark. Use `--dataset-version v2` for the new splits.

```sh
uv run --frozen python scripts/evaluate_rag.py --output /tmp/offline-eval.json
# Explicitly authorize sending corpus passages to Groq before a live run.
uv run --frozen python scripts/evaluate_rag.py --live --split tuning --limit 6 --output /tmp/tuning-eval.json
uv run --frozen python scripts/evaluate_rag.py --live --output /tmp/heldout-eval.json
```

Offline mode exercises query construction against a lexical fixture; it does not report live model quality, latency or cost. Live mode uses the same async classification, retrieval, generation and citation-validation functions, sequentially with a delay. It compares last-message-only and contextual retrieval on follow-ups, measures passage recall, gold-text checks, abstention, false refusal and quote provenance, and stops at the first provider error by default. It skips HTTP/quota handling, which has separate asserted tests. Runtime/corpus/prompt/dataset hashes and SDK/model settings are recorded; endpoint URLs, credentials and provider exception bodies are omitted. Set `COLLECTION_NAME=portfolio-live` only after the replacement alias is verified.

Live reports distinguish failed request duration from successful p50/p95 pipeline latency. The first observation and subsequent observations are reported separately; neither is described as a controlled provider or Vercel cold/warm benchmark. Cost uses a dated [Groq token-price snapshot](https://console.groq.com/docs/models), includes observed classifier/generator usage, and excludes storage, embeddings, Redis and hosting. It is an estimate, not a billing total; missing usage or failed calls mark the estimate incomplete. Both configured Groq models are currently listed as preview models, so access/lifecycle must be rechecked before rollout.

Automatic gold-text checks do not establish semantic support. To report supported-answer and semantic citation accuracy, review every answered fact against its quoted evidence, then supply `--reviews` with labels tied to the exact original result-file SHA256. `--summarize` reads an existing report without any provider requests. Without complete review, semantic metrics remain null.

## Tooling migration and advisory checks

The supported tooling is Vite 8 and ESLint 10 on Node 24. ESLint uses `eslint.config.js`; JSX references are tracked by ESLint itself, replacing the legacy React scope plugin. The Hooks plugin remains enabled. Vite 8 uses Rolldown/Oxc and Lightning CSS; no application transform options needed migration. See the official [Vite migration guide](https://vite.dev/guide/migration) and [ESLint 10 release notes](https://eslint.org/blog/2026/02/eslint-v10.0.0-released/). Servers stay bound to localhost.

```sh
npm audit
npm audit --omit=dev
uv run --no-project --with pip-audit pip-audit -r requirements.txt
uv run --no-project --with pip-audit pip-audit -r requirements-dev.txt
```

Keep runtime and development audit results separate. The October 2026 refresh updates advisory-affected Python transport packages and the local FastAPI/Starlette stack. UV constraints prevent affected HTTPX2 versions in optional tooling; the compatible lock currently uses LangSmith's HTTPX-based branch. Audit evidence is in `evals/checks/`; a clean audit is a database snapshot, not proof that dependencies are vulnerability-free.

The current account rejected a generation reservation of 1024 tokens against a reported 1000-token limit, even while aggregate rate headers showed 8000 available. Generation now reserves 768 tokens; the safeguard retains its separate 1024-token bound. Evaluation errors record only allowlisted rate headers. Groq may apply separate input/output quotas; aggregate headers are not sufficient to infer availability. No billing or quota upgrade was made.

## Hosted rollout checks

Project environment settings are server-side: configure `GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `FRONTEND_URL`, `COLLECTION_NAME=portfolio-live`, `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` for Production and Preview. Use distinct `CHAT_RATE_NAMESPACE` values for these environments. Changed environment settings require a new deployment. `VERCEL_TOKEN`, if used for administrative deployment access, stays in local configuration and must not be added to project environment variables.

The opt-in `python scripts/check_shared_quota.py --live --output /tmp/redis-check.json` uses three independent REST clients and unique expiring fixture namespaces on the configured Redis service. It checks simultaneous atomic admission, fresh-client continuity, TTL, lease release and real expiry without touching production visitor counters. Default execution makes no network requests. `evals/checks/shared-redis-hosted-2026-10-12.json` records a passing fixture with local-to-Redis timings. Actual Vercel routing, deployment duration, region latency and cold/warm HTTP observations remain separate rollout checks in FYP-97.
