"""Local browser-test fixture. Never calls Groq or Qdrant."""
import os
import json
from pathlib import Path
import sys
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('FRONTEND_URL', 'http://localhost:5173')
from api import chat
from scripts.dev_server import app


class FakeClient:
    def __init__(self):
        self.chat = NS(completions=NS(create=self.create))

    def with_options(self, **kwargs):
        return self

    async def create(self, model, messages, **kwargs):
        if 'safeguard' in model:
            answer = '{"violation":0}'
        else:
            question = messages[-1]['content']
            if question == 'simulate unavailable':
                raise chat.UpstreamUnavailable('Mock outage')
            if question == 'slow question':
                await asyncio.sleep(4)
            answer = json.dumps({'answer':'','supported':False,'evidence':[]}) if question == 'simulate unsupported' else json.dumps({'answer':'Mock documented answer to ' + question + ' [S1]', 'supported':True, 'evidence':[{'label':'S1','quote':'Public fixture documentation supports the mock answer.'}]})
        return NS(choices=[NS(finish_reason='stop', message=NS(content=answer, refusal=None))])


def main():
    import uvicorn
    @asynccontextmanager
    async def clients():
        yield None, FakeClient()
    chat.get_clients = clients
    async def retrieve(query, timeout=8, **kwargs):
        return [{'label':'S1','chunk_id':'mock-chunk','source':'test-project','project':'Test project','section':'Architecture','subsection':'','document_version':'a'*64,'score':0.8,'text':'Public fixture documentation supports the mock answer.'}]
    chat.retrieve = retrieve
    # Isolate transcript regression from the separately tested 10/minute quota.
    chat.RATE_LIMIT = 100
    uvicorn.run(app, host='127.0.0.1', port=8000)


if __name__ == '__main__':
    main()
