import { motion } from "framer-motion";

export default function About() {
  return (
    <section id="about">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <h2 style={{ fontSize: "3rem", marginBottom: "3rem" }}>
          About <span className="accent">Me</span>
        </h2>
      </motion.div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 400px), 1fr))",
          gap: "2rem",
          alignItems: "stretch",
        }}
      >
        {/* Left Card: Bio & Education */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          style={{ display: "flex" }}
        >
          <div
            className="card"
            style={{
              // THE FIX: Fluid padding so it doesn't crush content on mobile
              padding: "clamp(1.5rem, 5vw, 3rem)",
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div>
              <p
                style={{
                  fontSize: "1.4rem",
                  marginBottom: "1.5rem",
                  fontWeight: 600,
                  lineHeight: 1.4,
                }}
              >
                I am Qasim Tahir, a Data Science student at FAST-NUCES with a
                passion for <span className="accent">Generative AI</span> and{" "}
                <span className="accent">RAG</span>.
              </p>
              <p
                className="dim"
                style={{ fontSize: "1.1rem", marginBottom: "2.5rem" }}
              >
                My journey in AI is driven by the desire to make information
                more accessible and actionable. From building GraphRAG pipelines
                that understand research papers to creating multi-modal systems
                for religious scripture retrieval, I focus on building systems
                that don't just process data, but understand it.
              </p>
            </div>

            {/* THE FIX: Added flexWrap so badges can drop down if space gets too tight */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "1rem",
                borderTop: "1px solid var(--border)",
                paddingTop: "1.5rem",
                marginTop: "auto",
              }}
            >
              <div
                style={{
                  // THE FIX: flex: "1 1 auto" allows the badge to stretch evenly if it wraps
                  flex: "1 1 auto",
                  background: "var(--glass)",
                  padding: "1rem 1.5rem",
                  borderRadius: "16px",
                  border: "1px solid var(--glass-border)",
                }}
              >
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 800,
                    color: "var(--fg)",
                  }}
                >
                  BS DS
                </div>
                <div
                  className="dim"
                  style={{
                    fontSize: "0.75rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    fontWeight: 600,
                  }}
                >
                  Education
                </div>
              </div>
              <div
                style={{
                  // THE FIX: flex: "1 1 auto" applied here as well
                  flex: "1 1 auto",
                  background: "var(--glass)",
                  padding: "1rem 1.5rem",
                  borderRadius: "16px",
                  border: "1px solid var(--glass-border)",
                }}
              >
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 800,
                    color: "var(--fg)",
                  }}
                >
                  FAST
                </div>
                <div
                  className="dim"
                  style={{
                    fontSize: "0.75rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    fontWeight: 600,
                  }}
                >
                  University
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Right Card: Philosophy */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          style={{ position: "relative", display: "flex" }}
        >
          <div
            style={{
              background: "var(--accent-gradient)",
              width: "100%",
              height: "100%",
              borderRadius: "32px",
              opacity: 0.05,
              position: "absolute",
              top: "15px",
              left: "15px",
              zIndex: -1,
            }}
          />
          <div
            className="card"
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              padding: "clamp(1.5rem, 5vw, 3rem)", // Fluid padding applied here too
              textAlign: "center",
            }}
          >
            <h4
              style={{
                fontSize: "1rem",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                marginBottom: "1.5rem",
                color: "var(--accent)",
              }}
            >
              Core Philosophy
            </h4>
            <p
              style={{
                fontSize: "1.75rem",
                fontWeight: 600,
                fontStyle: "italic",
                lineHeight: 1.4,
                color: "var(--fg)",
              }}
            >
              "The most powerful AI systems are the ones that serve as an
              extension of human curiosity, not a replacement for it."
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
