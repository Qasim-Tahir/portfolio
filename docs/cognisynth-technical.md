# CogniSynth: implementation notes

## Scope
This is a scoped description from the public portfolio and supplied narrative. External performance measurements have not been supplied.

## Architecture
The owner describes PDF parsing with Docling, entity extraction with GLiNER and a Groq vision model, and canonical entity deduplication.

The described retrieval pipeline combines graph and text evidence, with BGE-M3 embeddings and BGE-Reranker-V2-M3.

The described answer checks compare extracted claims against retrieved text. They do not guarantee factual correctness.

## Historical evaluation scope
The supplied historical benchmark narrative has no evaluation date, sample size, exact provider model IDs or reproducible run artifacts in this repository. Conflicting GPT and Gemini labels were not relabeled as newer models. The old narrative is retained outside the indexed corpus for evidence review. No historical comparative ranking is established here.
