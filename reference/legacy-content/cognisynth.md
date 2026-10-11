# CogniSynth: GraphRAG + VLM Pipeline

## Overview

CogniSynth is a state-of-the-art hybrid pipeline designed for deep structural and visual understanding of academic research papers. It combines Knowledge Graph-based Retrieval Augmented Generation (GraphRAG) with Vision Language Models (VLMs) to extract relational context and visual data that traditional RAG systems often miss.

## Problem Statement

Standard vector search systems often fail to capture complex relationships between entities (e.g., "Model X uses Technique Y") and completely ignore critical information locked within figures, charts, and tables. Academic papers require a more nuanced, relational approach to truly understand the methodology and results.

## Architecture

The system consists of four primary modules:

1. **Knowledge Graph Pipeline**: Parses PDFs via Docling and extracts entities/relationships using a dual NER strategy (GLiNER + Groq Llama 4 Scout).
2. **Summarization Pipeline**: Generates field-by-field summaries using hybrid retrieval (Vector + Graph + Figure evidence).
3. **QA Engine**: Features HyDE query expansion, 2-hop graph neighborhood retrieval, and cross-encoder reranking.
4. **Verification Layer**: An LLM-based faithfulness checker that cross-references all citations against the source chunks.

## Key Technical Decisions

- **Dual NER Strategy**: Combined the speed of GLiNER for entity detection with the reasoning depth of Groq Llama 4 Scout for relationship extraction.

- **NER Strategy**: Qasim used a dual NER strategy combining GLiNER (a lightweight open-source NER model) and Groq Llama 4 for entity extraction. GLiNER handles fast local inference while
  Groq Llama 4 provides higher-accuracy extraction for complex entities.

- **Neo4j for Graph Storage**: Chosen for its robust Cypher query language, which allows for complex multi-hop relational retrieval.
- **BGE-M3 Embeddings & Rerankers**: Selected for their superior performance in technical and multilingual contexts.

## Implementation Details

- **Docling**: Used for high-fidelity document parsing and OCRM.
- **HybridChunker**: Splits documents into semantic units while preserving table and heading hierarchies.
- **Canonical Deduplication**: A custom normalization layer ensures that "DeepSeek-OCR" and "DeepSeek OCR" are treated as the same entity.

## Challenges & Solutions

- **Hallucinations**: Solved by implementing a citation-based verification pass where every claim must be grounded in a specific `[Ref: chunk_XXXXX]`.
- **Relational Gaps**: Bridged by Neo4j Cypher queries that retrieve the neighborhood of query entities, providing context that vector search alone cannot find.

## Tech Stack

- **Frameworks**: Docling, Neo4j, Groq API, LangChain
- **Models**: Llama 4 Scout (Inference), BGE-M3 (Embeddings), BGE-Reranker-V2-M3
- **Storage**: Neo4j (Graph), Vector Index

## Results & Outcomes

Achieved an 82.46% composite score on a custom 4-axis evaluation suite (Hit Rate, Faithfulness, Information Density, Structure), outperforming standard Gemini Flash and matching GPT-4o Pro in several key metric areas.

## FAQ

**Q: How did you handle hallucinations in CogniSynth?**
A: I implemented a mandatory two-pass system. The first pass generates the answer with specific chunk citations. The second pass extracts these claims and verifies them against the raw source text using an LLM judge.

**Q: Why use a Knowledge Graph instead of just Vector Search?**
A: Vector search is great for finding similar text but terrible at understanding relationships. If you ask "What dataset was used to train Model X?", a vector search might find a chunk mentioning both, but a graph query explicitly follows the `TRAINED_ON` edge to give a precise answer.

**Q: How does the VLM integration work?**
A: We use VLMs (like Llama 4 Scout) to generate technical descriptions of figures and charts. These descriptions are then stored as nodes in the graph and retrieved alongside text chunks during summarization.
