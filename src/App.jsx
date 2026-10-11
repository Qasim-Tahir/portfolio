import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence, MotionConfig, useReducedMotion } from "framer-motion";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import About from "./components/About";
import Experience from "./components/Experience";
import Skills from "./components/Skills";
import Projects from "./components/Projects";
import ChatBot from "./components/ChatBot";
import Contact from "./components/Contact";
import TerminalBoot from "./components/TerminalBoot";

function App() {
  const [isBooting, setIsBooting] = useState(true);
  const reducedMotion = useReducedMotion();
  const initialFragmentHandled = useRef(false);
  const restoreInitialFragment = () => {
    if (initialFragmentHandled.current) return;
    initialFragmentHandled.current = true;
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ behavior: "instant" });
  };
  useEffect(() => {
    if (isBooting) return;
    let frame;
    const restoreFragment = () => {
      cancelAnimationFrame(frame);
      // Run after native history restoration, including rapid section clicks
      // made before the preceding smooth scroll has completed.
      frame = requestAnimationFrame(() => {
        document.getElementById(window.location.hash.slice(1))?.scrollIntoView({
          behavior: reducedMotion ? "instant" : "smooth",
        });
      });
    };
    window.addEventListener("hashchange", restoreFragment);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("hashchange", restoreFragment);
    };
  }, [isBooting, reducedMotion]);

  return (
    <MotionConfig reducedMotion="user">
      <div className="app">
        <AnimatePresence mode="wait">
          {isBooting ? (
            <TerminalBoot
              key="bootScreen"
              onComplete={() => setIsBooting(false)}
            />
          ) : (
            <motion.div
              key="mainApp"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reducedMotion ? 0 : 0.8, ease: "easeOut" }}
            >
              <a className="skip-link" href="#main-content">Skip to content</a>
              <Nav />

              <motion.main
                id="main-content"
                tabIndex={-1}
                onAnimationComplete={restoreInitialFragment}
                initial={{ y: 20 }}
                animate={{ y: 0 }}
                transition={{ duration: reducedMotion ? 0 : 0.8, ease: "easeOut" }}
              >
                <Hero />
                <About />
                <Experience />
                <Skills />
                <Projects />
                <ChatBot />
                <Contact />
              </motion.main>
            </motion.div>
          )}
        </AnimatePresence>
        <Analytics />
        <SpeedInsights />
      </div>
    </MotionConfig>
  );
}

export default App;
