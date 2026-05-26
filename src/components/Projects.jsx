import { motion } from "framer-motion";
import {
  Microscope,
  FileText,
  Zap,
  BookOpen,
  Github,
  ExternalLink,
  ArrowRight,
} from "lucide-react";

const PROJECTS = [
  {
    title: "CogniSynth",
    desc: "Multi-modal GraphRAG + VLM pipeline for deep understanding of ML/AI research papers. Features dual NER and Neo4j relational retrieval.",
    tech: ["Neo4j", "Groq", "Docling", "Llama 3"],
    icon: <Microscope size={20} />,
    flow: ["PDFs", "VLM + NER", "Graph DB"],
    gradient:
      "linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 197, 253, 0.05) 100%)",
  },
  {
    title: "LuminaNotes",
    desc: "Vision-first OCR and academic summarization system. Processes PDFs, PPTX, and videos into Notion-ready study guides.",
    tech: ["Llama 3 Vision", "Whisper", "FastAPI"],
    icon: <FileText size={20} />,
    flow: ["Multi-modal", "OCR Agent", "Notion"],
    gradient:
      "linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(216, 180, 254, 0.05) 100%)",
  },
  {
    title: "Invoice Automation",
    desc: "End-to-end n8n workflow for structured data extraction from multi-format invoices using Vision-Language Models.",
    tech: ["n8n", "VLM", "Python"],
    icon: <Zap size={20} />,
    flow: ["Email/Doc", "n8n Flow", "JSON"],
    gradient:
      "linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(134, 239, 172, 0.05) 100%)",
  },
  {
    title: "Islamic Source Finder",
    desc: "Multi-modal semantic retrieval system for religious texts, supporting text, image, audio, and video queries.",
    tech: ["ChromaDB", "OCR", "Whisper"],
    icon: <BookOpen size={20} />,
    flow: ["Query", "Embedding", "Vector DB"],
    gradient:
      "linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(253, 224, 71, 0.05) 100%)",
  },
];

export default function Projects() {
  return (
    <section id="projects">
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

              {/* Action Links anchored to the bottom */}
              <div
                style={{
                  display: "flex",
                  gap: "1.5rem",
                  marginTop: "auto",
                  paddingTop: "1.5rem",
                  borderTop: "1px solid var(--border)",
                }}
              >
                <a
                  href="#"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    fontSize: "0.9rem",
                    fontWeight: 500,
                    color: "var(--text-dim)",
                  }}
                  className="hover:text-white transition-colors"
                >
                  <Github size={16} /> Code
                </a>
                <a
                  href="#"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    fontSize: "0.9rem",
                    fontWeight: 500,
                    color: "var(--accent)",
                  }}
                  className="hover:opacity-80 transition-opacity"
                >
                  <ExternalLink size={16} /> Live Demo
                </a>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
