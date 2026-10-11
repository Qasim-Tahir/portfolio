from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.requests import ClientDisconnect
import sys, os
import io
from dotenv import load_dotenv

# Ensure the root directory is in path for 'api.chat' import
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

env_path = os.path.join(ROOT_DIR, ".env.local")
load_dotenv(env_path)

app = FastAPI()

# Note: We REMOVED FastAPI's CORSMiddleware. 
# The CORS logic is now handled entirely by the 'api.chat.handler' 
# to ensure local and production behaviors are identical.

from api.chat import handler, MAX_BODY_SIZE, RequestError, content_length

class MockWfile:
    def __init__(self):
        self.data = io.BytesIO()
    def write(self, b):
        self.data.write(b)
    def getvalue(self):
        return self.data.getvalue()

class FastApiBridge(handler):
    def __init__(self, request: Request, body: bytes):
        self.request = request
        self.rfile = io.BytesIO(body)
        self.wfile = MockWfile()
        self.headers = request.headers
        self.path = request.url.path
        self.command = request.method
        self.client_address = (request.client.host, request.client.port) if request.client else ("127.0.0.1", 0)
        self.res_status = 200
        self.res_headers = {}

    def send_response(self, code, message=None):
        self.res_status = code

    def send_header(self, keyword, value):
        self.res_headers[keyword] = value

    def end_headers(self):
        pass

@app.post("/api/chat")
async def chat(request: Request):
    bridge = FastApiBridge(request, b"")
    try:
        # Reject the declared size first, then limit actual streamed bytes.
        # Missing lengths are valid for ASGI streams; the bridge receives the
        # measured length after buffering at most MAX_BODY_SIZE bytes.
        declared = content_length(request.headers, required=False)
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY_SIZE:
                raise RequestError(413, "Request body exceeds 32 KB")
            body.extend(chunk)
        if declared is not None and declared != len(body):
            raise RequestError(400, "Incomplete request body")
        bridge.rfile = io.BytesIO(body)
        headers = dict(request.headers)
        headers["content-length"] = str(len(body))
        headers.pop("transfer-encoding", None)
        bridge.headers = Headers(headers)
        await run_in_threadpool(bridge.do_POST)
    except RequestError as error:
        bridge._send_error(error.status, str(error))
    except ClientDisconnect:
        bridge._send_error(400, "Incomplete request body")
    
    return Response(
        content=bridge.wfile.getvalue(),
        status_code=bridge.res_status,
        headers=bridge.res_headers
    )

@app.options("/api/chat")
async def options(request: Request):
    bridge = FastApiBridge(request, b"")
    bridge.do_OPTIONS()
    return Response(
        content=bridge.wfile.getvalue(),
        status_code=bridge.res_status,
        headers=bridge.res_headers
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Unified Secure Dev Server starting on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
