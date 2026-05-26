# Portfolio Website & AI RAG Assistant

## Overview

This project is a premium personal portfolio website and interactive AI assistant built for Qasim Tahir to showcase his engineering work, skills, and projects. The chatbot is a live Retrieval-Augmented Generation (RAG) assistant that queries the site's own documentation to answer technical questions about Qasim's experience and architecture.

## Problem Statement

Recruiters and engineers viewing portfolios often have to skim through static bullet points or read long documents to gauge a candidate's fit. This project aims to demonstrate Qasim's actual RAG and AI engineering skills directly by embedding an advanced, production-grade, secure chatbot that behaves as an expert interface to his portfolio data.

## System Architecture

The project is built as a lightweight, production-ready Serverless RAG application:

1. **Frontend**: A high-performance React (Vite) single-page application deployed to Vercel's global edge network. It features a custom glassmorphic layout, fluid Framer Motion animations, and secure markdown formatting.
2. **Backend API**: A serverless Python function running at `/api/chat.py`, dynamically provisioned by Vercel. It handles CORS, rate limiting, request validation, injection filtering, semantic vector retrieval, and LLM orchestration.
3. **Vector Database**: Qdrant Cloud (managed cluster), which stores document chunks and serves semantic similarity queries with sub-second latency.
4. **LLM Inference**: Groq Cloud running `llama-3.1-8b-instant` for ultra-fast (sub-second) response generation.

## Key Design Decisions

- **Vercel Serverless Python**: Serves both frontend and backend on the same domain, eliminating complex CORS routing issues, and boots in under 2 seconds compared to traditional containers.
- **Fastembed Embeddings**: Uses Qdrant's Cloud Inference with `sentence-transformers/all-minilm-l6-v2` to keep the serverless deployment package under Vercel's 250MB size limit.
- **Strict Rate Limiting**: Implements IP-based rate limits to prevent API abuse, utilizing client IP tracking.
- **Input & Output Sanitization**: Protects against cross-site scripting (XSS) on the frontend via `rehype-sanitize` and restricts prompt leakage on the backend using regex and LLM safety checks.

## Tech Stack

- **Frontend**: React, Vite, Framer Motion, Lucide Icons, ReactMarkdown, Rehype-Sanitize.
- **Backend**: Python, FastAPI, Vercel Serverless, Uvicorn, Python-dotenv.
- **AI & Retrieval**: Qdrant Client, Groq API, LangChain.
- **Models**: `llama-3.1-8b-instant` (Inference), `all-minilm-l6-v2` (Embeddings).

## FAQ

**Q: How does the portfolio chatbot fetch its answers?**
A: When a user asks a question, the backend API first validates and cleans the input. It then generates a semantic embedding of the query and queries the Qdrant Cloud collection to retrieve the top 5 most relevant markdown documentation chunks. These chunks are injected as context into a system prompt that guides Groq Llama 3.1 to generate a precise, factual answer.

**Q: What makes this RAG pipeline production-ready?**
A: It includes production-grade security, such as:
1. Multi-layered prompt injection detection (deterministic Unicode filters + model-based safeguards).
2. Rate limiting to prevent denial-of-service or billing exhaustion.
3. Content-Type and payload verification to reject malformed requests.
4. Strict CORS policies.
5. Strict output validation to prevent system prompt leakage or environment variable exposure.
