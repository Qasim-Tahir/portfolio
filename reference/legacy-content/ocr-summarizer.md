# LuminaNotes: Multi-Modal OCR & Summarizer

## Overview

LuminaNotes is a sophisticated tool that converts diverse academic materials—PDFs, PPTX slide decks, hand-drawn images, and lecture videos—into structured, Notion-ready study guides and exam-focused Q&A pairs.

## Problem Statement

Traditional OCR tools often fail on complex academic layouts, including multi-column papers, mathematical LaTeX notations, and nested tables. Furthermore, students lack a way to automatically verify if an AI-generated summary is factually accurate relative to their specific lecture.

## Architecture

LuminaNotes uses a "Vision-First" approach:

1. **Ingestion**: Converts files to high-DPI images (300 DPI) for maximum OCR clarity.
2. **Extraction**: Uses Llama 4 Scout VLM via Groq to extract text while preserving mathematical symbols and table structures.
3. **Transcription**: Processes video/audio via Whisper-Large-v3.
4. **Refinement**: A regex-driven post-processing engine normalizes formatting.
5. **Summarization**: Generates condensed or full notes with automated exam question generation.

## Key Technical Decisions

- **Poppler-based Rendering**: Used `pdf2image` with Poppler for high-fidelity conversion of PDFs to images before OCR.
- **Headless LibreOffice**: Integrated to programmatically convert PPTX files to PDF, ensuring layout preservation.
- **Disk-based Caching**: Implemented a sliding-window batching strategy to process large documents without exceeding RAM limits.

## Implementation Details

- **LaTeX Support**: Specifically tuned system prompts to ensure the VLM returns mathematical notation in standard LaTeX format.
- **Table Normalization**: Handles broken Markdown table syntax by flattening complex headers into hierarchical sections.
- **Rate-Limit Resiliency**: A custom exponential backoff system that parses "retry-after" headers from the Groq API.

## Challenges & Solutions

- **Hallucination Drift**: Solved with a "Verification Pass" that isolates named entities (dates, names, formulas) in the summary and confirms their presence in the raw OCR output.
- **Video Processing**: Managed using `yt-dlp` and `moviepy` to isolate audio for Whisper transcription without needing to store large video files locally.

## Tech Stack

- **AI**: Groq (Llama 4 Scout VLM, Whisper), OpenAI Whisper
- **Processing**: pdf2image, Pillow, moviepy, LibreOffice
- **Runtime**: Python 3.12+

## Results & Outcomes

Achieved 100% layout fidelity for mathematical extraction and reduced manual note-taking time by approximately 60% for pilot users.

## FAQ

**Q: How do you handle mathematical formulas?**
A: By using a Vision-Language Model (Llama 4 Scout VLM) instead of traditional OCR (like Tesseract), the system understands the context of mathematical symbols and can output clean LaTeX code directly.

**Q: Can it process hand-written notes?**
A: Yes, as long as the handwriting is legible, the Llama 4 Scout VLM model is highly capable of transcribing hand-written text from images.

**Q: How is the summarization verified?**
A: Every generated summary undergoes a factual check where key entities are extracted and verified against the original OCR text. If an entity in the summary isn't found in the source, it's flagged for review.
