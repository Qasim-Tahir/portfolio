from dotenv import load_dotenv
import os
import json
import logging
import threading
import time
import asyncio
from contextlib import asynccontextmanager
import re
import unicodedata
from http.server import BaseHTTPRequestHandler
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Document
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from httpx import TimeoutException
from server.prompts import SYSTEM_PROMPT, SAFEGUARD_POLICY, GENERATION_MODEL, SAFEGUARD_MODEL, GENERATION_MAX_TOKENS
from server.evidence import strict_json, retrieval_query, evidence_record, generation_format, validated_answer, NO_EVIDENCE
from server.rate_limit import AsyncSharedLimiter, Settings, LimitExceeded, LimitUnavailable, client_identity, uses_shared_store
from groq import AsyncGroq, APITimeoutError, APIConnectionError, APIStatusError

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))


from server.config import EMBED_MODEL, collection_name
ALLOWED_ORIGIN = os.environ.get("FRONTEND_URL")
if not ALLOWED_ORIGIN:
    raise RuntimeError("FRONTEND_URL environment variable must be set")

# Security Constants
MAX_BODY_SIZE = 32_768  # 32KB
MAX_MESSAGES = 20
MAX_MESSAGE_LENGTH = 2000
MAX_ASSISTANT_LENGTH = 6000
REQUEST_BUDGET = 24  # seconds; browser deadline is 30 seconds
PROVIDER_TIMEOUT = 8
ALLOWED_ROLES = {"user", "assistant"}
RATE_LIMIT = 10         # requests per window
RATE_WINDOW = 60        # seconds

# Input-side: block before hitting any model
INJECTION_PATTERNS = [
    r'<<<',
    r'DUMP_START|DUMP_END',
    r'PRIORITY INTERRUPT',
    r'ADMIN_OVERRIDE',
    r'Authorization:\s*Bearer',
    r'NEW SYSTEM PROMPT FOLLOWS',
    r'IGNORE PREVIOUS',
    r'developer mode',
    r'unrestricted (ai|assistant|mode)',
    r'safety (team|scan|audit)',
    r'emergency override',
    r'system prompt (follows|below|starts)',
]

CREDENTIAL_PATTERNS = [r'gsk_[a-zA-Z0-9_-]{16,}', r'sk-[a-zA-Z0-9_-]{16,}']

# Output-side: block before reaching client
FORBIDDEN_OUTPUT_PATTERNS = [
    r'<<<.*?>>>',
    r'<system>.*?</system>',
    r'DUMP_START|DUMP_END',
    r'OVERRIDE SUCCESSFUL',
    r'SECURITY RULES\s*\(absolute',
    r'Your mission is to answer questions about Qasim Tahir',
]

# Common homoglyphs used in prompt injection attacks (maps to ASCII equivalents)
_CONFUSABLES = str.maketrans({
    # Greek → Latin
    '\u0391': 'A', '\u0392': 'B', '\u0395': 'E', '\u0396': 'Z', '\u0397': 'H',
    '\u0399': 'I', '\u039a': 'K', '\u039c': 'M', '\u039d': 'N', '\u039f': 'O',
    '\u03a1': 'P', '\u03a4': 'T', '\u03a5': 'Y', '\u03a7': 'X',
    '\u03b1': 'a', '\u03bf': 'o', '\u03c1': 'p',
    # Cyrillic → Latin
    '\u0410': 'A', '\u0412': 'B', '\u0421': 'C', '\u0415': 'E', '\u041d': 'H',
    '\u041a': 'K', '\u041c': 'M', '\u041e': 'O', '\u0420': 'P', '\u0422': 'T',
    '\u0425': 'X', '\u0423': 'Y',
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p', '\u0441': 'c',
    '\u0443': 'y', '\u0445': 'x',
    # Fullwidth → ASCII
    '\uff29': 'I', '\uff27': 'G', '\uff2e': 'N', '\uff2f': 'O', '\uff32': 'R',
    '\uff25': 'E', '\uff30': 'P', '\uff36': 'V',
})

def normalize_for_detection(text: str) -> str:
    """Normalize a detection copy; never modify the visitor's actual message."""
    text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad\u2060\u180e]', '', text)
    # NFKD normalization (handles accented characters)
    text = unicodedata.normalize('NFKD', text)
    # Map cross-script homoglyphs to ASCII (Greek Ι→I, Cyrillic А→A, etc.)
    text = text.translate(_CONFUSABLES)
    return ''.join(c for c in text if not unicodedata.combining(c))

def is_injection_attempt(query: str) -> bool:
    normalized = normalize_for_detection(query)
    # Compare both phrase and compact forms. Removing spaces from the query
    # alone loses word boundaries in zero-width and spaced-letter variants.
    compact = re.sub(r'\s+', '', normalized)
    for pattern in INJECTION_PATTERNS:
        compact_pattern = pattern.replace(' ', '').replace(r'\s*', '')
        if (re.search(pattern, normalized, re.IGNORECASE)
                or re.search(compact_pattern, compact, re.IGNORECASE)):
            return True
    return False

def contains_private_value(text: str) -> bool:
    # Actual deployment credentials are private. Public model names, stack
    # terms, project names, and public URLs are allowed.
    for name in ('GROQ_API_KEY', 'QDRANT_API_KEY', 'QDRANT_URL', 'UPSTASH_REDIS_REST_TOKEN', 'UPSTASH_REDIS_REST_URL'):
        secret = os.environ.get(name, '')
        if len(secret) >= 8 and secret in text:
            return True
    return any(re.search(pattern, text) for pattern in CREDENTIAL_PATTERNS)


def sanitize_reply(reply: str) -> tuple[bool, str]:
    if not isinstance(reply, str) or not reply.strip():
        raise UpstreamUnavailable('Empty generation')
    if contains_private_value(reply):
        return False, "I can only answer questions about Qasim's portfolio."
    for pattern in FORBIDDEN_OUTPUT_PATTERNS:
        if re.search(pattern, reply, re.IGNORECASE | re.DOTALL):
            return False, "I can only answer questions about Qasim's portfolio."
    return True, reply

# In-memory rate limiting
request_history = {}
rate_lock = threading.Lock()

@asynccontextmanager
async def get_clients():
    """Clients belong to one request/event loop and close on cancellation."""
    q_url = os.environ.get("QDRANT_URL")
    g_key = os.environ.get("GROQ_API_KEY")
    if not g_key or not q_url:
        raise UpstreamUnavailable("Chat is not configured")
    q = AsyncQdrantClient(url=q_url, api_key=os.environ.get("QDRANT_API_KEY"),
                          cloud_inference=True, timeout=PROVIDER_TIMEOUT)
    client = AsyncGroq(api_key=g_key, timeout=PROVIDER_TIMEOUT, max_retries=0)
    try:
        yield q, client
    finally:
        # Cleanup has its own one-second cap, below the 28-second platform cap.
        try:
            async with asyncio.timeout(1):
                results = await asyncio.gather(q.close(), client.close(), return_exceptions=True)
                if any(isinstance(result, BaseException) for result in results):
                    logging.warning("Chat client cleanup failed")
        except Exception:
            logging.warning("Chat client cleanup failed")

class RequestError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


class UpstreamUnavailable(Exception):
    pass


def content_length(headers, required=True):
    raw = headers.get("Content-Length")
    if raw is None and not required:
        return None
    if raw is None or not re.fullmatch(r"[0-9]+", raw):
        raise RequestError(400, "Invalid Content-Length")
    if len(raw.lstrip('0')) > len(str(MAX_BODY_SIZE)):
        raise RequestError(413, "Request body exceeds 32 KB")
    length = int(raw.lstrip('0') or '0')
    if length > MAX_BODY_SIZE:
        raise RequestError(413, "Request body exceeds 32 KB")
    return length


def validate_messages(body):
    if not isinstance(body, dict):
        raise RequestError(400, "Request body must be an object")
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise RequestError(400, "messages must be a non-empty list")
    if len(messages) > MAX_MESSAGES:
        raise RequestError(400, f"Too many messages (max {MAX_MESSAGES})")
    cleaned = []
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise RequestError(400, f"Message {i} must be an object")
        role, text = message.get("role"), message.get("content")
        if not isinstance(role, str) or role not in ALLOWED_ROLES:
            raise RequestError(400, f"Message {i} has invalid role")
        limit = MAX_MESSAGE_LENGTH if role == "user" else MAX_ASSISTANT_LENGTH
        if not isinstance(text, str) or not text.strip() or len(text) > limit:
            raise RequestError(400, f"Message {i} content invalid or too long")
        # Complete alternating turns, followed by the current user question.
        if role != ("user" if i % 2 == 0 else "assistant"):
            raise RequestError(400, "History must alternate user and assistant messages")
        cleaned.append({"role": role, "content": text})
    if cleaned[-1]["role"] != "user":
        raise RequestError(400, "Final message must be from the user")
    return cleaned


def remaining_timeout(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Chat deadline exceeded")
    return min(PROVIDER_TIMEOUT, remaining)


def read_body(stream, length, deadline, connection=None):
    chunks = bytearray()
    while len(chunks) < length:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Request body deadline exceeded")
        if connection is not None:
            connection.settimeout(remaining)
        # BufferedReader.read1 performs at most one underlying read. Checking
        # the deadline between reads also bounds a slowly trickled body.
        read = getattr(stream, 'read1', stream.read)
        chunk = read(length - len(chunks))
        if not chunk:
            break
        chunks.extend(chunk)
    return bytes(chunks)




async def retrieve(query: str, timeout=PROVIDER_TIMEOUT, *, client):
    q = client
    try:
        results = (await q.query_points(
            collection_name=collection_name(),
            query=Document(text=query, model=EMBED_MODEL),
            using="content_vector", limit=5, with_payload=True, timeout=max(1, int(timeout))
        )).points
    except ResponseHandlingException as error:
        if isinstance(error.source, (TimeoutError, TimeoutException)):
            raise TimeoutError("Retrieval timed out") from error
        raise UpstreamUnavailable("Retrieval unavailable") from error
    except UnexpectedResponse as error:
        raise UpstreamUnavailable("Retrieval unavailable") from error
    records = []
    try:
        for index, result in enumerate(results[:5], 1):
            record = evidence_record(result, index)
            # Screen all metadata as well as the body before sending it to a
            # model or displaying it. Public architecture names remain allowed.
            if any(contains_private_value(value) for value in record.values() if isinstance(value, str)):
                raise UpstreamUnavailable("Private data in retrieved payload")
            records.append(record)
    except (ValueError, TypeError, AttributeError) as error:
        raise UpstreamUnavailable("Invalid retrieved payload") from error
    return records


async def is_safe(messages, client, observer=None) -> bool:
    """Only an explicit complete safe verdict permits generation."""
    result = await client.chat.completions.create(
        model=SAFEGUARD_MODEL,
        messages=[{"role": "system", "content": SAFEGUARD_POLICY},
                  {"role": "user", "content": json.dumps(messages, ensure_ascii=False)}],
        temperature=0, max_completion_tokens=1024, stream=False
    )
    if observer:
        observer('safeguard', result)
    try:
        choice = result.choices[0]
        if choice.finish_reason != "stop" or getattr(choice.message, "refusal", None):
            raise ValueError("Incomplete verdict")
        verdict = strict_json(choice.message.content)
        if (not isinstance(verdict, dict) or set(verdict) != {"violation"}
                or type(verdict["violation"]) is not int
                or verdict["violation"] not in (0, 1)):
            raise ValueError("Invalid verdict schema")
        return verdict["violation"] == 0
    except (ValueError, TypeError, AttributeError, IndexError) as error:
        raise UpstreamUnavailable("Safeguard returned an invalid verdict") from error


REFUSAL = "I can only answer questions about Qasim's portfolio."
SOCIAL_REPLIES = {
    "hi": "Hi! Ask me about Qasim's projects, architecture, or experience.",
    "hello": "Hi! Ask me about Qasim's projects, architecture, or experience.",
    "hey": "Hi! Ask me about Qasim's projects, architecture, or experience.",
    "thanks": "You're welcome! You can ask about another part of Qasim's portfolio.",
    "thank you": "You're welcome! You can ask about another part of Qasim's portfolio.",
}


async def answer(messages, q, client, deadline, observer=None):
    safety_client = client.with_options(timeout=remaining_timeout(deadline), max_retries=0)
    if not await (is_safe(messages, safety_client, observer) if observer else is_safe(messages, safety_client)):
        return {"reply": REFUSAL, "sources": []}
    social = SOCIAL_REPLIES.get(messages[-1]['content'].strip().casefold().rstrip('.!?'))
    if social:
        return {"reply": social, "sources": [], "citations": []}
    records = await retrieve(retrieval_query(messages), remaining_timeout(deadline), client=q)
    if observer:
        observer('retrieval', records)
    if not records:
        return {"reply": NO_EVIDENCE, "sources": [], "citations": []}
    response = await client.with_options(timeout=remaining_timeout(deadline), max_retries=0).chat.completions.create(
        model=GENERATION_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT.format(context=json.dumps(records, ensure_ascii=False))}, *messages],
        response_format=generation_format(), max_completion_tokens=GENERATION_MAX_TOKENS, temperature=0.3
    )
    if observer:
        observer('generation', response)
    remaining_timeout(deadline)
    try:
        choice = response.choices[0]
        if choice.finish_reason != "stop" or getattr(choice.message, "refusal", None):
            raise ValueError("Incomplete generation")
        result = validated_answer(strict_json(choice.message.content), records)
    except (ValueError, AttributeError, IndexError, TypeError) as error:
        raise UpstreamUnavailable("Invalid generation response") from error
    is_clean, reply = sanitize_reply(result['reply'])
    if not is_clean or any(contains_private_value(citation['excerpt']) for citation in result['citations']):
        result = {"reply": REFUSAL, "sources": [], "citations": []}
    else:
        result['reply'] = reply
    return result


class handler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        if code == 429:
            self.send_header("Retry-After", str(getattr(self, "retry_after", RATE_WINDOW)))
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def _send_error(self, code, message):
        self._send_json(code, {"error": message})

    def do_POST(self):
        asyncio.run(self.handle_post())

    async def handle_post(self, deadline=None):
        deadline = deadline if deadline is not None else time.monotonic() + REQUEST_BUDGET
        limiter, lease_id = None, None
        try:
            async with asyncio.timeout(max(0, deadline - time.monotonic())):
                if self.path != '/api/chat':
                    raise RequestError(404, "Not found")
                if self.headers.get("Content-Type", "").split(';', 1)[0].strip().lower() != "application/json":
                    raise RequestError(415, "Content-Type must be application/json")
                if self.headers.get("Transfer-Encoding"):
                    raise RequestError(400, "Transfer-Encoding is not supported")
                length = content_length(self.headers)
                raw = read_body(self.rfile, length, deadline, getattr(self, 'connection', None))
                if len(raw) != length:
                    raise RequestError(400, "Incomplete request body")
                try:
                    body = strict_json(raw.decode('utf-8'))
                except (UnicodeDecodeError, ValueError, RecursionError) as error:
                    raise RequestError(400, "Invalid JSON") from error
                messages = validate_messages(body)

                client_ip = client_identity(self.headers, self.client_address[0])
                if uses_shared_store():
                    limiter = AsyncSharedLimiter(Settings.from_environment())
                    lease_id = await limiter.acquire(client_ip, min(2, remaining_timeout(deadline)))
                else:
                    # Explicit development-only fallback. Production requires the
                    # shared store and returns 503 if it is missing or unavailable.
                    now = time.monotonic()
                    with rate_lock:
                        expired = [ip for ip, hits in request_history.items() if not hits or now - hits[-1] >= RATE_WINDOW]
                        for ip in expired:
                            del request_history[ip]
                        hits = [t for t in request_history.get(client_ip, []) if now - t < RATE_WINDOW]
                        if len(hits) >= RATE_LIMIT:
                            raise RequestError(429, "Too many requests. Please wait a minute.")
                        request_history[client_ip] = [*hits, now]
                if any(is_injection_attempt(m['content']) or contains_private_value(m['content']) for m in messages):
                    self._send_json(200, {"reply": REFUSAL, "sources": []})
                    return
                async with get_clients() as (q, client):
                    result = await answer(messages, q, client, deadline)
            self._send_json(200, result)
        except LimitExceeded as error:
            self.retry_after = error.retry_after
            self._send_error(429, "Too many requests. Please try again shortly.")
        except RequestError as error:
            self._send_error(error.status, str(error))
        except (TimeoutError, APITimeoutError):
            self._send_error(504, "The response took too long. Please try again.")
        except (UpstreamUnavailable, LimitUnavailable, APIConnectionError, APIStatusError):
            self._send_error(503, "The chat service is temporarily unavailable. Please try again.")
        except Exception:
            # Provider exceptions can include request bodies or credentials.
            logging.error("Chat request failed")
            self._send_error(500, "Something went wrong. Please try again.")
        finally:
            if limiter is not None and lease_id is not None:
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    try:
                        await limiter.release(lease_id, min(1, remaining))
                    except LimitUnavailable:
                        # Lease expires even if the store is down or a worker dies.
                        logging.warning("Chat concurrency lease release failed")


    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
