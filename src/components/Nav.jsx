import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";

const NAV_LINKS = [
  { name: "About", href: "#about" },
  { name: "Experience", href: "#experience" },
  { name: "Skills", href: "#skills" },
  { name: "Projects", href: "#projects" },
  { name: "Contact", href: "#contact" },
];

export default function Nav() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Detect scroll to trigger the stronger glass effect
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const menuButtonRef = useRef(null);
  const menuRef = useRef(null);
  useEffect(() => {
    if (!isOpen) return;
    menuRef.current?.querySelector('a')?.focus();
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setIsOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    const handleResize = () => {
      if (window.innerWidth > 768) setIsOpen(false);
    };
    document.addEventListener("keydown", handleEscape);
    window.addEventListener("resize", handleResize);
    return () => {
      document.removeEventListener("keydown", handleEscape);
      window.removeEventListener("resize", handleResize);
    };
  }, [isOpen]);

  // Keep native anchor navigation, including modified clicks and history.
  const handleNavigation = (event) => {
    if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      setIsOpen(false);
    }
  };

  return (
    <>
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 2000,
          // THE FIX: Baseline glass effect at the top, heavy glass effect on scroll
          background: scrolled
            ? "rgba(10, 10, 10, 0.85)"
            : "rgba(10, 10, 10, 0.35)",
          backdropFilter: scrolled ? "blur(16px)" : "blur(8px)",
          WebkitBackdropFilter: scrolled ? "blur(16px)" : "blur(8px)",
          borderBottom: scrolled
            ? "1px solid rgba(255, 255, 255, 0.05)"
            : "1px solid transparent",
          transition: "all 0.3s ease",
        }}
      >
        <div className="nav-content">
          {/* THE FIX: Removed delayed entrance animations. */}
          <a
            href="#home"
            className="logo"
            style={{ cursor: "pointer" }}
          >
            Qasim Tahir
          </a>

          {/* Desktop Navigation */}
          <div className="nav-links">
            {NAV_LINKS.map((link) => (
              <motion.a
                key={link.name}
                href={link.href}
                onClick={handleNavigation}
                // We keep the hover effect, but remove the delayed initial/animate fade-in
                whileHover={{ color: "var(--fg)", y: -2 }}
                style={{
                  color: "var(--text-dim)",
                  textDecoration: "none",
                  fontWeight: 500,
                  transition: "color 0.2s", // Smooth transition returning from hover
                }}
              >
                {link.name}
              </motion.a>
            ))}
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="mobile-menu-btn"
            ref={menuButtonRef}
            aria-label={isOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={isOpen}
            aria-controls="mobile-navigation"
            onClick={() => setIsOpen(!isOpen)}
            style={{
              background: "none",
              border: "none",
              color: "var(--fg)",
              cursor: "pointer",
            }}
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            id="mobile-navigation"
            ref={menuRef}
            role="navigation"
            aria-label="Mobile navigation"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: "fixed",
              top: "70px",
              left: 0,
              right: 0,
              background: "rgba(18, 18, 18, 0.95)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              borderBottom: "1px solid var(--border)",
              padding: "2rem",
              display: "flex",
              flexDirection: "column",
              gap: "2rem",
              zIndex: 1999,
              alignItems: "center",
            }}
          >
            {NAV_LINKS.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={handleNavigation}
                style={{
                  color: "var(--text-dim)",
                  fontSize: "1.2rem",
                  fontWeight: 500,
                  textDecoration: "none",
                }}
              >
                {link.name}
              </a>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
