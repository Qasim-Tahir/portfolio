# AI Portfolio Engine: implementation notes

## Scope
This summary describes implementation in this repository.

## Architecture
The embedding model is sentence-transformers/all-minilm-l6-v2. Qdrant stores 384-dimensional cosine vectors named content_vector.

The API retrieves up to five passages and retains project, section, chunk ID, document version and similarity score. Follow-up queries use bounded recent user context.

Groq generation uses qwen/qwen3.8-27b and classification uses openai/gpt-oss-safeguard-20b. Configured IDs do not prove account access.

Selected citations must reference retrieved labels and include a verbatim quote. Validation proves quote provenance, not semantic entailment.

The API has a 24-second cancellable request budget, eight-second provider timeouts and no Groq retries. Browser requests have a 30-second deadline.

Production requires an atomic shared Redis quota. Defaults are ten requests per IP per minute, sixty requests globally per minute, and eight concurrent leases. Missing store configuration returns 503.

Corpus refresh builds and verifies a replacement collection before switching the portfolio-live alias, retaining old collections for rollback.

## Request validation
The API accepts JSON bodies up to 32768 bytes and at most twenty alternating user and assistant messages ending in a user message. User text is capped at 2000 characters; assistant text at 6000. The browser retains complete successful turns and bounds UTF-8 request bytes.

## Safety limits
Unicode normalization and injection-pattern checks run on a detection copy. The classifier permits only an explicit valid safe verdict. Known credential values and credential-shaped strings are screened. Prompt instructions and pattern filters reduce selected risks; they do not prove complete injection resistance. CORS controls browser access, not authentication or access by non-browser clients. Vercel supplies the trusted forwarded IP; direct local requests use the socket IP.
