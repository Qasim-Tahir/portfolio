# Chat browser regression

Run `uv run --frozen python tests/browser_server.py` and `npm run dev` in separate terminals. Open the Vite URL. The fixture binds only to localhost, uses fake providers, and raises the process quota to 100 requests per minute so transcript checks do not hit the separately tested 10/minute limit. It must not be used in deployment.

1. Let the existing boot animation complete, then open Ask AI Agent.
2. Send 12 distinct questions. After question 6, send `simulate unavailable`, verify a retry notice outside the transcript, and continue with question 7. Verify all 12 normal questions receive a mock answer and the complete visible transcript remains available.
3. Send `slow question`, close the panel while it is loading, and reopen it. Verify the cancellation notice, restored input, and enabled controls. The late answer must not appear.
4. Start another slow request and press New chat. Verify the greeting and starters return and no late answer enters the new conversation.
5. Verify input, send, close, and reset controls by keyboard, including Escape to close. Check that the chat and close control stay visible at widths 320, 375, 700, and 1024.
6. Stop both servers with Ctrl+C.

The automated tests cover malformed response schemas, rate-limit errors, deadlines, and late responses after reset. This browser fixture verifies rendering and event wiring; it does not evaluate real model safety, grounding, or provider latency. Existing page overflow and broader accessibility issues remain separate tickets.
