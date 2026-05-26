from fastapi import FastAPI, Request, Response
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

from api.chat import handler

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
    body = await request.body()
    bridge = FastApiBridge(request, body)
    bridge.do_POST()
    
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
