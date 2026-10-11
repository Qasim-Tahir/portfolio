import { motion } from "framer-motion";
import {
  Microscope,
  FileText,
  Zap,
  BookOpen,
  MessageSquare,
  Github,
  ExternalLink,
  ArrowRight,
} from "lucide-react";

const PROJECTS = [
  {
    title: "CogniSynth",
    repo: null,
    desc: "4-stage GraphRAG pipeline ingesting research papers into a Neo4j knowledge graph, with a two-pass VLM figure enrichment module and hallucination detection. Scored 82.46% composite on a custom 4-axis eval benchmarked against GPT-5.5 and Gemini 3.1 Pro via Ragas.",
    tech: ["Neo4j", "GraphRAG", "BGE-Reranker", "Ragas", "Three.js"],
    icon: <Microscope size={20} />,
    flow: ["PDFs", "VLM + NER", "Graph DB"],
    gradient:
      "linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 197, 253, 0.05) 100%)",
  },
  {
    title: "LuminaNotes",
    repo: "https://github.com/Qasim-Tahir/Lecture-Notes-Summarizer-OCR",
    desc: "Vision-first OCR and academic summarization system. Processes PDFs, PPTX, and videos into Notion-ready study guides.",
    tech: ["Llama 3 Vision", "Whisper", "FastAPI"],
    icon: <FileText size={20} />,
    flow: ["Multi-modal", "OCR Agent", "Notion"],
    gradient:
      "linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(216, 180, 254, 0.05) 100%)",
  },
  {
    title: "Invoice Automation",
    repo: null,
    desc: "End-to-end n8n workflow for structured data extraction from multi-format invoices using Vision-Language Models.",
    tech: ["n8n", "VLM", "Python"],
    icon: <Zap size={20} />,
    flow: ["Email/Doc", "n8n Flow", "JSON"],
    gradient:
      "linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(134, 239, 172, 0.05) 100%)",
  },
  {
    title: "Islamic Source Finder",
    repo: "https://github.com/Qasim-Tahir/IslamicSourceFinder",
    desc: "Multi-modal semantic retrieval system for religious texts, supporting text, image, audio, and video queries.",
    tech: ["ChromaDB", "OCR", "Whisper"],
    icon: <BookOpen size={20} />,
    flow: ["Query", "Embedding", "Vector DB"],
    gradient:
      "linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(253, 224, 71, 0.05) 100%)",
  },
  {
    title: "AI Portfolio Engine",
    repo: "https://github.com/Qasim-Tahir/portfolio",
    demo: "chat",
    desc: "This site's RAG chatbot: Qdrant and Groq over project documentation, with inspectable source passages. It validates requests and citation quotes, classifies conversations, and applies injection-pattern filters.",
    tech: ["Qdrant", "Groq", "LangChain", "Vercel"],
    icon: <MessageSquare size={20} />,
    flow: ["Docs", "RAG + Security", "Chat UI"],
    gradient:
      "linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(251, 182, 206, 0.05) 100%)",
  },
];

export default function Projects({ onOpenChat }) {
  return (
    <section tabIndex={-1} id="projects">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 style={{ fontSize: "3rem", marginBottom: "1rem" }}>
          Featured <span className="accent">Projects</span>
        </h2>
        <p
          className="dim"
          style={{
            fontSize: "1.1rem",
            marginBottom: "4rem",
            maxWidth: "600px",
          }}
        >
          A collection of systems designed to bridge the gap between raw data
          and actionable intelligence.
        </p>
      </motion.div>

      <div
        style={{
          display: "grid",
          // THE FIX: Changed from 340px to min(100%, 300px) so it never overflows narrow mobile screens
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 300px), 1fr))",
          gap: "2.5rem",
          alignItems: "stretch",
        }}
      >
        {PROJECTS.map((project, i) => (
          <motion.div
            key={project.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            style={{ display: "flex", height: "100%" }}
          >
            <div
              className="card"
              style={{
                width: "100%",
                // Optional mobile refinement: fluid padding so the card doesn't look overly tight on small phones
                padding: "clamp(1.5rem, 5vw, 2rem)",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {/* Visual Architecture Header */}
              <div
                style={{
                  background: project.gradient,
                  border: "1px solid var(--border)",
                  borderRadius: "16px",
                  padding: "clamp(1rem, 4vw, 1.5rem)", // Fluid padding here too for tight text
                  marginBottom: "2rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                {/* Background watermark icon */}
                <div
                  style={{
                    position: "absolute",
                    right: "-10%",
                    top: "50%",
                    transform: "translateY(-50%)",
                    opacity: 0.05,
                    color: "var(--fg)",
                  }}
                >
                  {project.icon}
                </div>

                {/* Data Flow Pipeline */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    width: "100%",
                    justifyContent: "center",
                    zIndex: 1,
                    // Ensuring text wrapping behaves nicely on narrow screens
                    flexWrap: "wrap",
                    textAlign: "center",
                  }}
                >
                  <span
                    style={{
                      fontSize: "clamp(0.7rem, 2.5vw, 0.8rem)", // Fluid text
                      fontWeight: 600,
                      color: "var(--text-dim)",
                    }}
                  >
                    {project.flow[0]}
                  </span>
                  <ArrowRight size={14} className="dim" />
                  <span
                    style={{
                      fontSize: "clamp(0.7rem, 2.5vw, 0.8rem)",
                      fontWeight: 600,
                      color: "var(--accent)",
                    }}
                  >
                    {project.flow[1]}
                  </span>
                  <ArrowRight size={14} className="dim" />
                  <span
                    style={{
                      fontSize: "clamp(0.7rem, 2.5vw, 0.8rem)",
                      fontWeight: 600,
                      color: "var(--fg)",
                    }}
                  >
                    {project.flow[2]}
                  </span>
                </div>
              </div>

              {/* Project Content */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ color: "var(--accent)" }}>{project.icon}</div>
                <h3 style={{ fontSize: "1.4rem" }}>{project.title}</h3>
              </div>

              <p
                className="dim"
                style={{
                  marginBottom: "2rem",
                  fontSize: "0.95rem",
                  lineHeight: 1.6,
                }}
              >
                {project.desc}
              </p>

              {/* Tech stack pills */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.4rem",
                  marginBottom: "2rem",
                }}
              >
                {project.tech.map((t) => (
                  <span key={t} className="tech-pill">
                    {t}
                  </span>
                ))}
              </div>

              <div className="project-actions">
                {project.repo ? (
                  <a href={project.repo} target="_blank" rel="noopener noreferrer"
                    aria-label={`View ${project.title} source code on GitHub`}
                    className="project-code-link">
                    <Github size={16} /> Code
                  </a>
                ) : (
                  <span className="project-unavailable" aria-label={`${project.title} source code unavailable`}>
                    <Github size={16} /> Code unavailable
                  </span>
                )}
                {project.demo === "chat" ? (
                  <button onClick={onOpenChat} className="project-demo-link"
                    aria-label="Open AI Portfolio Engine demo chat">
                    <ExternalLink size={16} /> Live Demo
                  </button>
                ) : (
                  <span className="project-unavailable" aria-label={`${project.title} demo unavailable`}>
                    <ExternalLink size={16} /> Demo unavailable
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
