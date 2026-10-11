"""Local browser-test fixture. Never calls Groq or Qdrant."""
import os
from pathlib import Path
import sys
import time
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

    def create(self, model, messages, **kwargs):
        if 'safeguard' in model:
            answer = '{"violation":0}'
        else:
            question = messages[-1]['content']
            if question == 'simulate unavailable':
                raise chat.UpstreamUnavailable('Mock outage')
            if question == 'slow question':
                time.sleep(4)
            answer = 'Mock documented answer to ' + question
        return NS(choices=[NS(finish_reason='stop', message=NS(content=answer, refusal=None))])


def main():
    import uvicorn
    chat.get_clients = lambda: (None, FakeClient())
    chat.retrieve = lambda query, timeout=8: ('Public fixture documentation.', ['test-project'])
    # Isolate transcript regression from the separately tested 10/minute quota.
    chat.RATE_LIMIT = 100
    uvicorn.run(app, host='127.0.0.1', port=8000)


if __name__ == '__main__':
    main()
