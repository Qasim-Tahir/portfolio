import { validateCitations } from "./citations.js";

export const MAX_INPUT_LENGTH = 2000;
export const CHAT_TIMEOUT_MS = 30_000;
const MAX_BODY_BYTES = 32_768;

export class ChatError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ChatError";
    this.status = status;
  }
}

export function requestMessages(history, question) {
  if (!question.trim() || question.length > MAX_INPUT_LENGTH) {
    throw new ChatError(`Enter a question of at most ${MAX_INPUT_LENGTH} characters.`, 400);
  }
  // Keep complete turns, reserving one slot for the current user message.
  const messages = [...history.slice(-18), { role: "user", content: question }];
  while (new TextEncoder().encode(JSON.stringify({ messages })).length > MAX_BODY_BYTES) {
    if (messages.length === 1) throw new ChatError("Your question is too large. Please shorten it.", 413);
    messages.splice(0, 2);
  }
  return messages;
}

function statusMessage(status, retryAfter) {
  if (status === 429) {
    const seconds = Number(retryAfter);
    return seconds > 0 && Number.isFinite(seconds)
      ? `Too many requests. Try again in ${Math.ceil(seconds)} seconds.`
      : "Too many requests. Wait a minute and try again.";
  }
  if (status === 400 || status === 413 || status === 415) return "Your message could not be accepted. Please shorten or rephrase it.";
  if (status === 504) return "The response took too long. Please try again.";
  return "The chat service is temporarily unavailable. Please try again.";
}

// Only successful exchanges enter API history. Local greetings, errors, and
// canceled questions stay in the UI and never consume the server's quota.
export class ChatSession {
  constructor(fetchImpl = (url, options) => globalThis.fetch(url, options), timeoutMs = CHAT_TIMEOUT_MS) {
    this.fetchImpl = fetchImpl;
    this.timeoutMs = timeoutMs;
    this.history = [];
    this.active = null;
  }

  cancel() {
    this.active?.abort();
    this.active = null;
  }

  reset() {
    this.cancel();
    this.history = [];
  }

  async send(question) {
    if (this.active) throw new ChatError("A request is already in progress.");
    const messages = requestMessages(this.history, question);
    const controller = new AbortController();
    this.active = controller;
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.timeoutMs);
    const canceled = new Promise((_, reject) => {
      controller.signal.addEventListener("abort", () => reject(new ChatError(
        timedOut ? "The response took too long. Please try again." : "Request canceled. You can try again.",
        timedOut ? 504 : 0,
      )), { once: true });
    });
    try {
      const result = await Promise.race([
        (async () => {
          const response = await this.fetchImpl("/api/chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messages }), signal: controller.signal,
          });
          if (!response.ok) throw new ChatError(statusMessage(response.status, response.headers.get("Retry-After")), response.status);
          let data;
          try {
            data = await response.json();
          } catch {
            throw new ChatError("The service returned an invalid response. Please try again.", 503);
          }
          if (!data || typeof data !== "object" || typeof data.reply !== "string" || !data.reply.trim() || data.reply.length > 6000
              || !Array.isArray(data.sources) || data.sources.some(source => typeof source !== "string")) {
            throw new ChatError("The service returned an invalid response. Please try again.", 503);
          }
          let citations;
          try {
            citations = validateCitations(data);
          } catch {
            throw new ChatError("The service returned invalid source passages. Please try again.", 503);
          }
          return { ...data, citations };
        })(),
        canceled,
      ]);
      if (controller.signal.aborted || this.active !== controller) throw new ChatError("Request canceled. You can try again.");
      this.history = [...messages, { role: "assistant", content: result.reply }];
      return result;
    } catch (error) {
      if (error instanceof ChatError) throw error;
      throw new ChatError("Could not connect to chat. Check your connection and try again.");
    } finally {
      clearTimeout(timer);
      if (this.active === controller) this.active = null;
    }
  }
}
