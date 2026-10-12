import asyncio
import io
import os
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api import chat
from test_chat import invoke, VALID, clients_for


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        chat.request_history.clear()

    def test_body_deadline_checks_each_underlying_read(self):
        stream=MagicMock()
        stream.read1.return_value=b'x'
        conn=MagicMock()
        with patch.object(chat.time,'monotonic',side_effect=[0, .6, 1.1]):
            with self.assertRaises(TimeoutError):
                chat.read_body(stream, 3, 1, conn)
        self.assertEqual(stream.read1.call_count,2)
        self.assertEqual(conn.settimeout.call_count,2)

    def test_pending_shared_quota_is_cancelled_before_providers(self):
        cancelled=[]
        async def stall(*args):
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.append(True)
        limiter=NS(acquire=AsyncMock(side_effect=stall),release=AsyncMock())
        with patch.object(chat,'REQUEST_BUDGET',.03), patch.object(chat,'uses_shared_store',return_value=True), patch.object(chat.Settings,'from_environment'), patch.object(chat,'AsyncSharedLimiter',return_value=limiter), patch.object(chat,'get_clients') as providers:
            self.assertEqual(invoke(VALID)[0],504)
        self.assertEqual(cancelled,[True])
        providers.assert_not_called()
        limiter.release.assert_not_called()

    def test_request_clients_close_on_cancellation(self):
        q=NS(close=AsyncMock())
        g=NS(close=AsyncMock())
        async def run():
            with patch.dict(os.environ,{'GROQ_API_KEY':'test-key','QDRANT_URL':'https://example.test'}), patch.object(chat,'AsyncQdrantClient',return_value=q), patch.object(chat,'AsyncGroq',return_value=g):
                with self.assertRaises(TimeoutError):
                    async with asyncio.timeout(.02):
                        async with chat.get_clients():
                            await asyncio.sleep(10)
        asyncio.run(run())
        q.close.assert_awaited_once()
        g.close.assert_awaited_once()


if __name__=='__main__': unittest.main()
