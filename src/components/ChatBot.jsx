import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Send, X, Bot, User, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { ChatSession, MAX_INPUT_LENGTH } from "../lib/chatSession";

const GREETING = { role: "assistant", content: "Hi! I'm a live RAG pipeline running on Qdrant + Groq, querying Qasim's actual project documentation. Ask me anything technical about his work." };

const STARTERS = [
  "How is the knowledge graph built in CogniSynth?",
  "How did you handle hallucinations in the OCR project?",
  "Explain the error handling in the Invoice Automation.",
  "What vision models are used in the OCR summarizer?",
];

export default function ChatBot({ openRequest = 0 }) {
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showStarters, setShowStarters] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  // NEW: State to control the tooltip visibility
  const [showTooltip, setShowTooltip] = useState(false);

  const reducedMotion = useReducedMotion();
  const launcherRef = useRef(null);
  const restoreFocusRef = useRef(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const chatWindowRef = useRef(null);
  const sessionRef = useRef(null);
  if (!sessionRef.current) sessionRef.current = new ChatSession();
  const requestIdRef = useRef(0);
  const pendingQuestionRef = useRef("");
  const [error, setError] = useState("");

  function closeChat(returnFocus = false) {
    restoreFocusRef.current = returnFocus;
    requestIdRef.current += 1;
    if (sessionRef.current.active) {
      sessionRef.current.cancel();
      setInput(pendingQuestionRef.current);
      setError("Request canceled. You can try again.");
      setLoading(false);
    }
    setIsOpen(false);
  }

  function resetChat() {
    requestIdRef.current += 1;
    sessionRef.current.reset();
    setMessages([GREETING]);
    setInput("");
    setError("");
    setLoading(false);
    setShowStarters(true);
  }

  useEffect(() => {
    if (!openRequest) return;
    setIsOpen(true);
    setShowTooltip(false);
  }, [openRequest]);
  useEffect(() => () => sessionRef.current.cancel(), []);
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        chatWindowRef.current &&
        !chatWindowRef.current.contains(event.target)
      ) {
        closeChat();
      }
    }
    function handleEscape(event) {
      if (event.key === "Escape") closeChat(true);
    }
    // Only bind the listener if the chat is actually open
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: reducedMotion ? "instant" : "smooth" });
  }, [messages, loading, reducedMotion]);

  useEffect(() => {
    if (isOpen && !loading) {
      inputRef.current?.focus();
    }
  }, [isOpen, loading]);

  // NEW: Trigger the tooltip 5 seconds after the component mounts
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isOpen) setShowTooltip(true);
    }, 5000);
    return () => clearTimeout(timer);
  }, [isOpen]);

  async function send(text) {
    const userMsg = (text || input).trim();
    if (!userMsg || sessionRef.current.active) return;
    if (userMsg.length > MAX_INPUT_LENGTH) {
      setError(`Enter a question of at most ${MAX_INPUT_LENGTH} characters.`);
      return;
    }
    const requestId = ++requestIdRef.current;
    pendingQuestionRef.current = userMsg;
    setInput("");
    setError("");
    setShowStarters(false);
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const data = await sessionRef.current.send(userMsg);
      if (requestId !== requestIdRef.current) return;
      setMessages(prev => [...prev, { role: "assistant", content: data.reply, sources: data.sources, citations: data.citations }]);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setError(err.message);
      setInput(userMsg);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }

  return (
    <>
      {/* Injecting the pulse keyframes directly so you don't need to edit CSS */}
      <style>
        {`
          @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
          }
        `}
      </style>

      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            style={{
              position: "fixed",
              bottom: "2rem",
              right: "2rem",
              zIndex: 3000,
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: "1rem",
            }}
          >
            {/* 1. The Delayed "Peek" Tooltip */}
            <AnimatePresence>
              {showTooltip && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.9 }}
                  style={{
                    background: "var(--glass)",
                    backdropFilter: "blur(12px)",
                    border: "1px solid var(--glass-border)",
                    padding: "1rem",
                    borderRadius: "16px",
                    width: "260px",
                    boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
                    display: "flex",
                    gap: "0.75rem",
                    alignItems: "flex-start",
                  }}
                >
                  <p
                    style={{
                      fontSize: "0.85rem",
                      lineHeight: 1.5,
                      color: "var(--fg)",
                      margin: 0,
                    }}
                  >
                    I'm a live{" "}
                    <span className="accent" style={{ fontWeight: 600 }}>
                      RAG pipeline
                    </span>
                    . Ask me how Qasim's architecture works.
                  </p>
                  <button
                    aria-label="Dismiss chat hint"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowTooltip(false);
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-dim)",
                      cursor: "pointer",
                      padding: "2px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <X size={16} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 2. Main Button with Pulse */}
            <button
              className="btn btn-primary"
              ref={launcherRef}
              aria-haspopup="dialog"
              aria-controls="portfolio-chat"
              onClick={() => {
                setIsOpen(true);
                setShowTooltip(false); // Hide tooltip instantly when opened
              }}
              style={{
                padding: "1rem 2rem",
                gap: "0.8rem",
                borderRadius: "20px",
                display: "flex",
                alignItems: "center",
                animation: "pulse-ring 3s infinite", // Applies the CSS animation
              }}
            >
              <Sparkles size={20} />
              Ask AI Agent
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence onExitComplete={() => {
        if (restoreFocusRef.current) launcherRef.current?.focus();
        restoreFocusRef.current = false;
      }}>
        {isOpen && (
          <motion.div
            ref={chatWindowRef}
            className="chat-container"
            id="portfolio-chat"
            role="dialog"
            aria-modal="false"
            aria-label="Portfolio chat"
            initial={{ opacity: 0, y: 100, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.8 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
          >
            <div
              className="chat-header"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                }}
              >
                <div
                  style={{
                    background: "var(--accent-gradient)",
                    padding: "8px",
                    borderRadius: "12px",
                  }}
                >
                  <Bot size={20} color="#fff" />
                </div>
                <div>
                  <div className="chat-title">Project RAG Engine</div>
                  <div className="chat-meta">Qdrant · Groq · Qwen3</div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <button className="chat-reset" onClick={resetChat}>New chat</button>
              <button
                aria-label="Close chat"
                onClick={() => closeChat(true)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                }}
              >
                <X size={20} />
              </button>
              </div>
            </div>

            <div className="chat-messages" role="log" aria-live="polite" aria-relevant="additions" aria-busy={loading}>
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`msg ${m.role}`}
                  style={{
                    display: "flex",
                    gap: "0.75rem",
                    flexDirection: m.role === "user" ? "row-reverse" : "row",
                  }}
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background:
                        m.role === "user"
                          ? "var(--accent)"
                          : "var(--glass-border)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {m.role === "user" ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: m.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "calc(100% - 44px)",
                    }}
                  >
                    <div className="bubble">
                      <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                        {m.content}
                      </ReactMarkdown>
                    </div>

                    {m.citations?.length > 0 ? (
                      <div className="sources citation-list" aria-label="Answer evidence">
                        {m.citations.map(citation => (
                          <details key={citation.label} className="citation">
                            <summary>
                              <span className="badge">[{citation.label}]</span>{" "}
                              {citation.project} · {citation.section || citation.source}
                            </summary>
                            <blockquote>{citation.excerpt}</blockquote>
                            <p>{citation.source}{citation.subsection ? ` · ${citation.subsection}` : ""}</p>
                            <p>Document version: {citation.document_version || "unavailable for this legacy document"}</p>
                            <p>Chunk: {citation.chunk_id}</p>
                            <p>Retrieval similarity: {citation.score.toFixed(3)}. This score does not verify the answer.</p>
                          </details>
                        ))}
                      </div>
                    ) : m.sources?.length > 0 && (
                      <div className="sources">
                        Retrieved documents (passages unavailable):{" "}
                        {m.sources.map(source => <span key={source} className="badge">{source}</span>)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div
                  className="msg assistant"
                  style={{ display: "flex", gap: "0.75rem" }}
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: "var(--glass-border)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Bot size={16} />
                  </div>
                  <div className="bubble typing" role="status" aria-label="Generating response">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {showStarters && (
              <div className="starters">
                {STARTERS.map((s) => (
                  <button key={s} onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}

            {error && <div className="chat-error" role="alert">{error}</div>}
            <div className="chat-input">
              <input
                aria-label="Question about Qasim's projects"
                maxLength={MAX_INPUT_LENGTH}
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.nativeEvent.isComposing && send()}
                placeholder="Ask about my AI projects..."
                disabled={loading}
              />
              <button
                aria-label="Send message"
                onClick={() => send()}
                disabled={loading || !input.trim()}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Send size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
