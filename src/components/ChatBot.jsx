import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Send, X, Bot, User, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

const STARTERS = [
  "How is the knowledge graph built in CogniSynth?",
  "How did you handle hallucinations in the OCR project?",
  "Explain the error handling in the Invoice Automation.",
  "What vision models are used in the OCR summarizer?",
];

export default function ChatBot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm a live RAG pipeline running on Qdrant + Groq, querying Qasim's actual project documentation. Ask me anything technical about his work.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showStarters, setShowStarters] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  // NEW: State to control the tooltip visibility
  const [showTooltip, setShowTooltip] = useState(false);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const chatWindowRef = useRef(null);
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        chatWindowRef.current &&
        !chatWindowRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }
    // Only bind the listener if the chat is actually open
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;
    setInput("");
    setShowStarters(false);
    const newMessages = [...messages, { role: "user", content: userMsg }];
    setMessages(newMessages);
    setLoading(true);
    inputRef.current?.focus();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });

      // Guard: if Vercel returns a non-200 (404, 500, etc.), it's likely HTML, not JSON.
      if (!res.ok) {
        const errorText = await res.text();
        console.error(`API Error ${res.status}:`, errorText);
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();

      if (data.error) throw new Error(data.error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          sources: data.sources,
        },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I'm having trouble connecting to my knowledge base right now. Please ensure the API keys are correctly configured.",
        },
      ]);
    }
    setLoading(false);
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

      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={chatWindowRef}
            className="chat-container"
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
                  <div className="chat-meta">Qdrant · Groq · Llama 3.1</div>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
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

            <div className="chat-messages">
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

                    {m.sources && m.sources.length > 0 && (
                      <div className="sources">
                        Sources:{" "}
                        {m.sources.map((s) => (
                          <span
                            key={s}
                            className="badge"
                            style={{ marginLeft: "4px" }}
                          >
                            {s}
                          </span>
                        ))}
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
                  <div className="bubble typing">
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

            <div className="chat-input">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Ask about my AI projects..."
                disabled={loading}
              />
              <button
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
