import { motion } from "framer-motion";
import { BrainCircuit, Database, Server, Wrench } from "lucide-react";

const SKILLS = [
  {
    category: "AI/ML",
    icon: <BrainCircuit size={20} />,
    items: [
      "LangChain",
      "LlamaIndex",
      "LangGraph",
      "HuggingFace",
      "Neo4j",
      "PyTorch",
      "TensorFlow",
    ],
  },
  {
    category: "Vector DBs",
    icon: <Database size={20} />,
    items: ["Qdrant", "ChromaDB", "FAISS", "Pinecone"],
  },
  {
    category: "Backend",
    icon: <Server size={20} />,
    items: ["FastAPI", "Flask", "Node.js", "Docker", "Azure", "PostgreSQL"],
  },
  {
    category: "Tools",
    icon: <Wrench size={20} />,
    items: ["n8n", "Groq", "Git", "Linux"],
  },
];

export default function Skills() {
  return (
    <section id="skills">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 style={{ fontSize: "3rem", marginBottom: "4rem" }}>
          Technical <span className="accent">Arsenal</span>
        </h2>
      </motion.div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "2rem",
        }}
      >
        {SKILLS.map((skill, i) => (
          <motion.div
            key={skill.category}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: i * 0.05 }}
            style={{ display: "flex", height: "100%" }}
          >
            {/* The CSS .card class is now safely on the inner div */}
            <div
              className="card"
              style={{
                width: "100%",
                padding: "2.5rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-start",
                gap: "1.5rem",
              }}
            >
              <h3
                style={{
                  fontSize: "1.25rem",
                  color: "var(--fg)",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  margin: 0,
                }}
              >
                <span style={{ color: "var(--accent)" }}>{skill.icon}</span>
                {skill.category}
              </h3>

              <div
                style={{
                  display: "flex",
                  flexDirection: "row",
                  flexWrap: "wrap",
                  alignItems: "flex-start",
                  alignContent: "flex-start",
                  gap: "0.6rem",
                }}
              >
                {skill.items.map((item) => (
                  <span key={item} className="tech-pill">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
