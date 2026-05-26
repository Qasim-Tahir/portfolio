import { useEffect } from "react";
import { motion } from "framer-motion";

const terminalContainer = {
  hidden: { opacity: 1 },
  visible: {
    transition: { staggerChildren: 0.15, delayChildren: 0.3 },
  },
};

const typeLine = {
  hidden: { clipPath: "inset(0 100% 0 0)", opacity: 0 },
  visible: {
    clipPath: "inset(0 0% 0 0)",
    opacity: 1,
    transition: { duration: 0.25, ease: "linear" },
  },
};

const cursorVariant = {
  hidden: { opacity: 0 },
  visible: {
    opacity: [0, 1, 0],
    transition: { repeat: Infinity, duration: 0.8, ease: "linear" },
  },
};

export default function TerminalBoot({ onComplete }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, 3700);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <motion.div
      exit={{ opacity: 0, filter: "blur(10px)" }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "#000000",
        zIndex: 9999,
        // THE FIX: Reduced minimum padding so code has more room to breathe on mobile
        padding: "clamp(1rem, 5vw, 4rem)",
        fontFamily: "'Fira Code', 'Courier New', Courier, monospace",
        // THE FIX: Fluid font size. Caps at 18px on desktop, shrinks to 12px on tiny phones
        fontSize: "clamp(12px, 3.5vw, 18px)",
        lineHeight: "1.6",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        justifyContent: "flex-start",
        overflow: "hidden",
      }}
    >
      <motion.div
        variants={terminalContainer}
        initial="hidden"
        animate="visible"
        // PURE WHITE BASE TEXT FOR MAXIMUM CONTRAST
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.2rem",
          color: "#ffffff",
        }}
      >
        <motion.div
          variants={typeLine}
          style={{
            color: "#a8b2c1",
            fontStyle: "italic",
            marginBottom: "1rem",
          }}
        >
          [system] Initializing RAG Portfolio Engine...
        </motion.div>

        <motion.div variants={typeLine}>
          <span style={{ color: "#ff2a7f" }}>from</span> portfolio.agent{" "}
          <span style={{ color: "#ff2a7f" }}>import</span>{" "}
          <span style={{ color: "#00e6ff" }}>RAG_Assistant</span>
        </motion.div>

        <motion.div variants={typeLine}>
          <span style={{ color: "#ff2a7f" }}>from</span> models{" "}
          <span style={{ color: "#ff2a7f" }}>import</span>{" "}
          <span style={{ color: "#00e6ff" }}>Groq</span>,{" "}
          <span style={{ color: "#00e6ff" }}>Qdrant</span>
        </motion.div>

        <motion.div variants={typeLine} style={{ height: "0.8em" }} />

        <motion.div
          variants={typeLine}
          style={{ color: "#a8b2c1", fontStyle: "italic" }}
        >
          # Initialize Portfolio Assistant
        </motion.div>

        <motion.div variants={typeLine}>
          agent = <span style={{ color: "#00e6ff" }}>RAG_Assistant</span>(
        </motion.div>

        <motion.div variants={typeLine}>
          &nbsp;&nbsp;&nbsp;&nbsp;llm=
          <span style={{ color: "#00e6ff" }}>Groq</span>(model=
          <span style={{ color: "#39ff14" }}>"llama-3.1-8b"</span>),
        </motion.div>

        <motion.div variants={typeLine}>
          &nbsp;&nbsp;&nbsp;&nbsp;vector_db=
          <span style={{ color: "#00e6ff" }}>Qdrant</span>(collection=
          <span style={{ color: "#39ff14" }}>"portfolio-rag"</span>)
        </motion.div>

        <motion.div variants={typeLine}>)</motion.div>

        <motion.div variants={typeLine} style={{ height: "0.8em" }} />

        <motion.div
          variants={typeLine}
          style={{ color: "#a8b2c1", fontStyle: "italic" }}
        >
          # Ingest Qasim's project documentation
        </motion.div>

        <motion.div variants={typeLine}>
          agent.ingest(
          <span style={{ color: "#39ff14" }}>"docs/projects/"</span>)
        </motion.div>

        <motion.div variants={typeLine}>agent.deploy()</motion.div>

        <motion.div variants={typeLine} style={{ height: "1.2em" }} />

        <motion.div
          variants={typeLine}
          style={{ color: "#00e6ff", fontWeight: "bold" }}
        >
          &gt; RAG Pipeline Active.
        </motion.div>

        <motion.div
          variants={typeLine}
          style={{ color: "#39ff14", fontWeight: "bold" }}
        >
          &gt; Interface Ready. Routing traffic...
        </motion.div>

        <motion.div
          variants={cursorVariant}
          style={{
            width: "12px",
            height: "1.2em",
            background: "#ffffff", // Pure white cursor
            marginTop: "0.5rem",
          }}
        />
      </motion.div>
    </motion.div>
  );
}
