# Portfolio RAG Technical & Security hardener

## Backend Architecture

The backend consists of a single serverless Python function (`api/chat.py`) running on Vercel. 
The handler subclasses Python's `BaseHTTPRequestHandler` to provide a raw, lightweight, dependencies-optimized HTTP interface, keeping the Vercel cold-start times extremely low.

### Semantic Ingestion Pipeline
- **Document Chunking**: Structured markdown project files under `docs/` are parsed using `MarkdownHeaderTextSplitter` to isolate sections (e.g., `## Overview`, `## Architecture`) and then chunked via `RecursiveCharacterTextSplitter` with a chunk size of 500 characters and an overlap of 80 characters.
- **Qdrant Cloud Inference**: Ingestion utilizes Qdrant's managed cloud embeddings endpoint. We send raw text chunks directly to Qdrant, referencing the `sentence-transformers/all-minilm-l6-v2` model. Qdrant handles embedding computation internally before storing vectors, removing the need to install heavy ML packages (like PyTorch or HuggingFace) on the serverless endpoint.
- **Named Vectors**: Stored vectors are mapped under the name `content_vector`.

---

## 4-Layer Security Hardening System

To prevent LLM jailbreaks, system prompt extraction, indirect injection, and denial-of-service, a custom 4-Layer Security Hardening System is implemented directly within `api/chat.py`:

**Layer 1: Deterministic Unicode Normalization & Pattern Matching**
Traditional injection filters fail against obfuscated prompts (e.g., zero-width spaces or Unicode homoglyphs). 
- **Zero-Width Space Stripping**: The engine strips invisible characters (e.g., `\u200b`, `\u200c`, `\ufeff`) that are used to disrupt pattern detectors.
- **Homoglyph Translation**: Map table (`maketrans`) resolves Cyrillic (e.g., Cyrillic `А` -> Latin `A`) and Greek (e.g., Greek `Ι` -> Latin `I`) homoglyphs back to ASCII before inspection.
- **Spaced Letter Collapsing**: Removes extra spaces inserted between individual characters of key injection terms (e.g., `I G N O R E` -> `IGNORE`).
- **Pattern Scanner**: Scans all messages in the conversation history (not just the final user message) against known malicious patterns (e.g., `IGNORE PREVIOUS`, `NEW SYSTEM PROMPT`, `ADMIN_OVERRIDE`).

**Layer 2: Model-Based Safeguard (Llama-Guard)**
- A secondary, lightweight LLM safety shield model (`openai/gpt-oss-safeguard-20b`) is queried to analyze the user's intent.
- **Fail-Closed Design**: If the safeguard model fails, times out, or hits rate limits, the request is immediately blocked by default.

**Layer 3: Persona Hardening**
- The system instructions are designed with high-weight rules that explicitly instruct the model to prioritize safety rules over all retrieved context, user prompts, or system overrides. It is taught to never reveal its instructions or environment variables.

**Layer 4: Output Sanitization**
- Prior to writing the response to the client, the final answer is validated against strict blacklisted regex patterns.
- If the output contains forbidden terms (such as `gsk_`, `sk-`, `QDRANT_URL`, `.env`, `<system>`), it is intercepted, blocked, and replaced with a safe fallback response to prevent API keys or internal structures from leaking.

---

## Access Control & Infrastructure Defense

### CORS & Origin Validation
- Wildcard CORS is disabled. The server strictly validates the `Origin` header against the production `FRONTEND_URL` environment variable during preflight (`OPTIONS`) and actual requests.

### Client IP Rate Limiting & Anti-Spoofing
- **Quota**: 10 requests per 60 seconds per unique IP.
- **Anti-Spoofing**: To prevent attackers from setting arbitrary `X-Forwarded-For` headers to get fresh rate-limit buckets, the backend parses `X-Forwarded-For` by extracting the rightmost entry. Vercel appends the true client IP at the very end of this header, ensuring spoofed IPs in the header are bypassed.

### Input Payload Validation
- Enforces a maximum request body size of 32KB.
- Rejects requests without `application/json` Content-Type.
- Limits the message list to 20 entries.
- Limits individual message contents to 2000 characters.
- Requires role to be either `user` or `assistant`.
- Rejects nested structures or non-string values inside the message `content` field.
