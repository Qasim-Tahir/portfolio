import { motion } from "framer-motion";
import {
  Mail,
  Github,
  Linkedin,
  MapPin,
  ExternalLink,
  Cpu,
} from "lucide-react";

export default function Contact() {
  return (
    <section
      id="contact"
      style={{ position: "relative", paddingBottom: "2rem" }}
    >
      {/* Subtle background glow to anchor the bottom of the page */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "100%",
          height: "100%",
          background:
            "radial-gradient(circle at center, rgba(59, 130, 246, 0.05) 0%, transparent 60%)",
          zIndex: -1,
          pointerEvents: "none",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: "center", marginBottom: "4rem" }}
      >
        <h2 style={{ fontSize: "3rem", marginBottom: "1rem" }}>
          Let's <span className="accent">Connect</span>
        </h2>
        <p
          className="dim"
          style={{
            fontSize: "1.1rem",
            maxWidth: "600px",
            margin: "0 auto",
            lineHeight: 1.6,
          }}
        >
          Currently open for AI Software Engineering and Data & AI Intern roles.
          Whether you have a question about my RAG pipelines or want to build
          something impactful together, my inbox is open.
        </p>
      </motion.div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "2rem",
          maxWidth: "900px",
          margin: "0 auto",
        }}
      >
        {/* Left Card: Direct Contact */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          style={{ display: "flex", height: "100%" }}
        >
          {/* THE FIX: Inner div handles the CSS .card class */}
          <div
            className="card"
            style={{
              width: "100%",
              padding: "3rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                background: "var(--accent-soft)",
                color: "var(--accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1.5rem",
              }}
            >
              <Mail size={28} />
            </div>
            <h3 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
              Get in Touch
            </h3>
            <p
              className="dim"
              style={{ marginBottom: "2.5rem", fontSize: "0.95rem" }}
            >
              I try my best to respond to all inquiries within 24 hours.
            </p>

            <button
              onClick={() => {
                const user = "qasimbtahir"; // Replace with your actual username
                const domain = "gmail.com"; // Replace with your actual domain
                window.location.href = `mailto:${user}@${domain}`;
              }}
              className="btn btn-primary"
              style={{ width: "100%", padding: "1rem", cursor: "pointer" }}
            >
              Say Hello
            </button>
          </div>
        </motion.div>

        {/* Right Card: Digital Presence & Socials */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          style={{ display: "flex", height: "100%" }}
        >
          {/* THE FIX: Inner div handles the CSS .card class */}
          <div
            className="card"
            style={{
              width: "100%",
              padding: "3rem",
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            <h3
              style={{
                fontSize: "1.25rem",
                marginBottom: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <Cpu size={20} className="accent" /> Digital Presence
            </h3>

            <SocialLink
              href="https://github.com/Qasim-Tahir"
              icon={<Github size={20} />}
              label="GitHub"
              showArrow={true}
            />
            <SocialLink
              href="https://www.linkedin.com/in/qasim-tahir-300267201/"
              icon={<Linkedin size={20} />}
              label="LinkedIn"
              showArrow={true}
            />
            <SocialLink
              href="#"
              icon={<MapPin size={20} />}
              label="Lahore, Pakistan"
              showArrow={false}
            />
          </div>
        </motion.div>
      </div>

      {/* Footer Section */}
      <motion.div
        style={{
          marginTop: "6rem",
          paddingTop: "2rem",
          borderTop: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, delay: 0.4 }}
      >
        <div className="logo" style={{ fontSize: "1.2rem" }}>
          Qasim Tahir
        </div>
        <p className="dim" style={{ fontSize: "0.9rem" }}>
          © {new Date().getFullYear()} Designed & Engineered by Qasim Tahir.
        </p>
      </motion.div>
    </section>
  );
}

// Reusable micro-component for the social links to keep the code DRY
function SocialLink({ href, icon, label, showArrow }) {
  const isLink = href !== "#";
  const Component = isLink ? motion.a : motion.div;

  return (
    <Component
      href={isLink ? href : undefined}
      target={isLink ? "_blank" : undefined}
      rel={isLink ? "noreferrer" : undefined}
      whileHover={
        isLink
          ? {
              scale: 1.02,
              backgroundColor: "rgba(255,255,255,0.08)",
              borderColor: "rgba(255,255,255,0.25)",
            }
          : {}
      }
      transition={{ duration: 0.2 }}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "1rem 1.5rem",
        background: "var(--glass)",
        border: "1px solid var(--glass-border)",
        borderRadius: "16px",
        color: "var(--fg)",
        textDecoration: "none",
        cursor: isLink ? "pointer" : "default",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {icon}
        <span style={{ fontWeight: 500, fontSize: "0.95rem" }}>{label}</span>
      </div>
      {showArrow && <ExternalLink size={16} className="dim" />}
    </Component>
  );
}
