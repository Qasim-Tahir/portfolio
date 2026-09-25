import { motion } from "framer-motion";
import {
  Users,
  FileCode2,
  Bot,
  ShieldCheck,
  Rocket,
  ArrowRight,
  Mic,
  BrainCircuit,
  BarChart3,
  Activity,
} from "lucide-react";

const WORKFLOW_STEPS = [
  { label: "Stakeholder Needs", icon: <Users size={18} /> },
  { label: "Engineering Spec", icon: <FileCode2 size={18} /> },
  { label: "Claude-Code-Directed Build", icon: <Bot size={18} /> },
  { label: "Review, Debug & Secure", icon: <ShieldCheck size={18} /> },
  { label: "Production Deploy", icon: <Rocket size={18} /> },
];

const HIGHLIGHTS = [
  {
    title: "AI-Powered Internal ERP",
    desc: "Own the translation of stakeholder requirements into engineering specs, and direct AI-assisted development end-to-end with Claude Code — architecture, implementation review, debugging, security validation, and production deployment. Resolved 115+ tickets as the primary technical owner.",
    icon: <FileCode2 size={20} />,
  },
  {
    title: "Automated AI Screening Voice Agent",
    desc: "Built an AI-driven voice agent that conducts and screens candidate interviews automatically, cutting down manual first-pass screening effort.",
    icon: <Mic size={20} />,
  },
  {
    title: "Company Second Brain",
    desc: "Contributed to an org-wide knowledge ingestion and triage pipeline pulling from email, calendar, meetings, and messaging into a review inbox, with LLM-based triage surfacing what matters.",
    icon: <BrainCircuit size={20} />,
  },
  {
    title: "KPI Dashboard Data Integrity",
    desc: "Diagnosed and fixed a silent SQL aggregation bug in a company-wide KPI/analytics dashboard that was dropping ~95% of records in one metric.",
    icon: <BarChart3 size={20} />,
  },
  {
    title: "AI Pipeline Reliability",
    desc: "Fixed production AI reliability issues in the KPI pipeline, including a broken model-fallback path that silently failed assessments when API credits ran out, and non-deterministic scoring that produced inconsistent results from identical inputs.",
    icon: <Activity size={20} />,
  },
];

export default function Experience() {
  return (
    <section id="experience">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 style={{ fontSize: "3rem", marginBottom: "1rem" }}>
          Work <span className="accent">at TST</span>
        </h2>
        <p
          className="dim"
          style={{
            fontSize: "1.1rem",
            marginBottom: "3rem",
            maxWidth: "650px",
          }}
        >
          As a Junior AI Engineer at The Services Tree, I sit between
          stakeholders and the codebase — turning requirements into shipped,
          secure AI systems.
        </p>
      </motion.div>

      {/* Workflow Diagram */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="card"
        style={{
          padding: "clamp(1.5rem, 5vw, 2.5rem)",
          marginBottom: "2.5rem",
        }}
      >
        <h4
          style={{
            fontSize: "0.85rem",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            color: "var(--text-dim)",
            marginBottom: "1.75rem",
          }}
        >
          Stakeholder-to-Production Workflow
        </h4>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.75rem",
          }}
        >
          {WORKFLOW_STEPS.map((step, i) => (
            <div
              key={step.label}
              style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "0.6rem",
                  padding: "1rem 1.25rem",
                  background: "var(--glass)",
                  border: "1px solid var(--glass-border)",
                  borderRadius: "16px",
                  minWidth: "130px",
                  textAlign: "center",
                }}
              >
                <span style={{ color: "var(--accent)" }}>{step.icon}</span>
                <span
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    color: "var(--fg)",
                  }}
                >
                  {step.label}
                </span>
              </div>
              {i < WORKFLOW_STEPS.length - 1 && (
                <ArrowRight size={16} className="dim" />
              )}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Highlight Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
          gap: "2rem",
          alignItems: "start",
        }}
      >
        {HIGHLIGHTS.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="card"
            style={{
              padding: "clamp(1.5rem, 5vw, 2rem)",
              justifyContent: "flex-start",
              gap: "1rem",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
              }}
            >
              <span style={{ color: "var(--accent)" }}>{item.icon}</span>
              <h3 style={{ fontSize: "1.1rem" }}>{item.title}</h3>
            </div>
            <p className="dim" style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>
              {item.desc}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
