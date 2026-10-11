# Chat browser regression

Run `uv run --frozen python tests/browser_server.py` and `npm run dev` in separate terminals. Open the Vite URL. The fixture binds only to localhost, uses fake providers, and raises the process quota to 100 requests per minute so transcript checks do not hit the separately tested 10/minute limit. It must not be used in deployment.

1. Let the existing boot animation complete, then open Ask AI Agent.
2. Send 12 distinct questions. After question 6, send `simulate unavailable`, verify a retry notice outside the transcript, and continue with question 7. Verify all 12 normal questions receive a mock answer and the complete visible transcript remains available.
3. Send `slow question`, close the panel while it is loading, and reopen it. Verify the cancellation notice, restored input, and enabled controls. The late answer must not appear.
4. Start another slow request and press New chat. Verify the greeting and starters return and no late answer enters the new conversation.
5. Verify input, send, close, and reset controls by keyboard, including Escape to close. Check that the chat and close control stay visible at widths 320, 375, 700, and 1024.
6. Stop both servers with Ctrl+C.

The automated tests cover malformed response schemas, rate-limit errors, deadlines, and late responses after reset. This browser fixture verifies rendering and event wiring; it does not evaluate real model safety, grounding, or provider latency.

## Responsive, keyboard, and navigation regression

1. At widths 320, 375, 600, 601, 700, 768, 769, and 1280, visit Skills and Contact and let their entrance animations finish. Confirm each section's content fits and the document scroll width equals its client width. The Skills grid uses one column through 768, two through 991, and three above that; wide cards must not create implicit tracks. Confirm every hero word fits, with the second line wrapping on narrow screens.
2. Check chat at those widths. Up to 600 it has 16px margins and height `100dvh - 32px`; above 600 it stays 400px wide by 600px tall, capped at 80vh, with 32px offsets. The 700px layout is deliberately the same as desktop, with no competing 768px rule.
3. Tab to the skip link and activate it. Confirm focus reaches the main landmark. Activate the logo and section links by keyboard, checking focus outlines and native fragments. Open the mobile menu: its expanded state must change and the first link receives focus. Escape closes it and returns focus to the toggle. Tab remains free to move through the nonmodal menu and chat.
4. Open chat and verify input focus, labeled controls, live response/status/error regions, and a nonmodal dialog. Escape and Close return focus to Ask AI Agent after the exit animation. An outside click must keep focus on the clicked page control.
5. Send a normal message and inspect the rendered user bubble: white text on rgb(37, 99, 235) measures 5.17:1. User links and emphasis inherit white; links are underlined. Confirm the surrounding palette is unchanged.
6. Open a direct `/#skills` URL, let the mandatory boot finish, and confirm the section starts about 90px from the viewport top. Click Projects, go Back to Skills, and Forward to Projects; wait for normal smooth scrolling to finish before measuring. Headings must clear the fixed 70px navigation.
7. Enable the browser's reduced-motion preference and repeat navigation and boot. Terminal text remains visible for the same mandatory boot interval; its reveal and blinking cursor, ambient CSS effects, smooth scrolling, and motion transforms are disabled. Normal animation remains unchanged when the preference is off.
