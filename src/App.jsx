import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import Nav from "./components/Nav";
import Hero from "./components/Hero";
import About from "./components/About";
import Skills from "./components/Skills";
import Projects from "./components/Projects";
import ChatBot from "./components/ChatBot";
import Contact from "./components/Contact";
import TerminalBoot from "./components/TerminalBoot";

function App() {
  const [isBooting, setIsBooting] = useState(true);

  return (
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
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <Nav />

            <motion.div
              initial={{ y: 20 }}
              animate={{ y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <Hero />
              <About />
              <Skills />
              <Projects />
              <ChatBot />
              <Contact />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
