import { motion } from "framer-motion";
import { ArrowRight, Terminal, Download } from "lucide-react";

const textContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.1 },
  },
};

const wordItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
  },
};

const buttonFadeVariant = {
  hidden: { opacity: 0, y: 15 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: 0.7, ease: "easeOut" },
  },
};

const WordReveal = ({ text }) => {
  const words = text.split(" ");
  return (
    <>
      {words.map((word, i) => (
        <motion.span
          key={i}
          variants={wordItem}
          style={{
            display: "inline-block",
            marginRight: "0.25em",
            whiteSpace: "nowrap",
          }}
        >
          {word}
        </motion.span>
      ))}
    </>
  );
};

export default function Hero() {
  return (
    <section
      className="hero"
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        width: "100%",
        minHeight: "90vh",
        // THE FIX: Allow vertical bleeding, prevent horizontal scrollbars
        overflowX: "clip",
        overflowY: "visible",
      }}
    >
      <style>
        {`
          @keyframes ambient-drift-1 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(5%, 5%) scale(1.1); }
          }
          @keyframes ambient-drift-2 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(-5%, -5%) scale(1.05); }
          }
        `}
      </style>

      {/* Dynamic Ambient AI Background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "30%",
            width: "50vw",
            height: "50vw",
            background:
              "radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 60%)",
            animation: "ambient-drift-1 15s ease-in-out infinite",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "0%", // Lowered slightly so it bleeds nicely
            right: "20%",
            width: "60vw",
            height: "60vw",
            background:
              "radial-gradient(circle, rgba(147, 51, 234, 0.05) 0%, transparent 60%)",
            animation: "ambient-drift-2 20s ease-in-out infinite reverse",
          }}
        />
      </div>

      {/* Centered Hero Content */}
      <motion.div
        variants={textContainerVariants}
        initial="hidden"
        animate="visible"
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: "1000px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "0 1rem",
        }}
      >
        <h1
          style={{
            marginBottom: "2rem",
            // THE FIX: Lowered the minimum font size from 2.5rem to 1.8rem
            // This guarantees the single line won't get chopped on mobile screens
            fontSize: "clamp(1.8rem, 8vw, 5.5rem)",
            lineHeight: "1.1",
            letterSpacing: "-0.02em",
            fontWeight: "800",
          }}
        >
          <div style={{ display: "block" }}>
            <WordReveal text="AI/ML Engineer" />
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flexWrap: "nowrap",
              whiteSpace: "nowrap",
              marginTop: "0.1em",
            }}
          >
            <span
              style={{
                background: "var(--accent-gradient)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                display: "inline-block",
                paddingBottom: "0.2em",
                marginBottom: "-0.2em",
              }}
            >
              <WordReveal text="Building" />
            </span>
            <span style={{ marginLeft: "0.25em" }}>
              <WordReveal text="the Future." />
            </span>
          </div>
        </h1>

        <motion.p
          variants={wordItem}
          style={{
            fontSize: "clamp(1.1rem, 2vw, 1.25rem)",
            lineHeight: "1.6",
            marginBottom: "3.5rem",
            color: "var(--text-dim)",
            maxWidth: "650px",
            fontWeight: "400",
          }}
        >
          Specializing in Multi-modal RAG pipelines, Knowledge Graphs, and
          High-Performance AI Automations.
        </motion.p>

        <motion.div
          variants={buttonFadeVariant}
          className="hero-actions"
          style={{
            display: "flex",
            gap: "1rem",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          <button
            className="btn btn-primary"
            onClick={() => document.getElementById("projects").scrollIntoView()}
            style={{ padding: "0.8rem 1.8rem", fontSize: "1rem" }}
          >
            View Projects <ArrowRight size={18} />
          </button>

          {/* THE CV BUTTON */}
          <a
            href="/resume.pdf"
            download="Qasim_Tahir_Resume.pdf"
            className="btn btn-secondary"
            style={{
              padding: "0.8rem 1.8rem",
              fontSize: "1rem",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Download size={18} /> Resume
          </a>

          <button
            className="btn btn-secondary"
            onClick={() => document.getElementById("about").scrollIntoView()}
            style={{ padding: "0.8rem 1.8rem", fontSize: "1rem" }}
          >
            <Terminal size={18} /> About Me
          </button>
        </motion.div>
      </motion.div>
    </section>
  );
}
