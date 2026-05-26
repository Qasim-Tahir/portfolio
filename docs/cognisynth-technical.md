# CogniSynth: GraphRAG + VLM Pipeline for Academic Paper Understanding

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [File-by-File Breakdown](#3-file-by-file-breakdown)
4. [Knowledge Graph Pipeline](#4-knowledge-graph-pipeline)
5. [Summarization Pipeline](#5-summarization-pipeline)
6. [QA Engine](#6-qa-engine)
7. [Benchmarking and Evaluation](#7-benchmarking-and-evaluation)
8. [Technologies and Dependencies](#8-technologies-and-dependencies)
9. [Execution Guide](#9-execution-guide)
10. [Implementation Details](#10-implementation-details)
11. [Research and Technical Insights](#11-research-and-technical-insights)
12. [Project Context File](#12-project-context-file)

---

## 1. Project Overview

### Purpose

CogniSynth is a hybrid pipeline combining **GraphRAG** (Knowledge Graph-based Retrieval Augmented Generation) with **VLM** (Vision Language Models) for comprehensive academic paper understanding. The system processes PDF research papers through multiple stages: document parsing, entity extraction, knowledge graph construction, summarization, and question-answering.

### Core Objectives

- **Accurate Information Extraction**: Extract structured entities, relationships, and metrics from unstructured academic papers
- **Multi-Modal Understanding**: Handle both text and figures/diagrams using VLMs
- **Graph-Based Context**: Build knowledge graphs in Neo4j for relational context beyond simple chunk retrieval
- **Comprehensive Summarization**: Generate field-by-field paper summaries using hybrid retrieval
- **Question Answering**: Enable precise Q&A over paper content with citation verification

### Problems Being Solved

- Academic papers contain dense technical information hard to extract with simple chunking
- Standard vector search misses relational facts between entities (e.g., "Model X uses Technique Y")
- Figures and tables carry critical data not captured by text-only extraction
- Faithfulness verification is needed to prevent hallucinated answers

### High-Level Workflow

```
PDF Input
    │
    ▼
┌─────────────────┐
│  kg2.py         │ ← Document Parsing (Docling) + Chunking (HybridChunker)
│  Knowledge Graph│ ← Entity Extraction (GLiNER + Groq NER)
│  Pipeline       │ ← Relationship Extraction
└────────┬────────┘
         │ Neo4j KG + Chunk Embeddings
         ▼
┌─────────────────┐     ┌──────────────────┐
│ summarize.py    │ ←─── │ richy.py (VLM)   │
│ Summarization   │      │ Figure Parsing   │
│ Pipeline        │      └──────────────────┘
└────────┬────────┘
         │ Summary + GraphRAG Context
         ▼
┌─────────────────┐
│ qa_engine.py    │
│ QA Engine       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ eval_summary.py │
│ Evaluation      │
└─────────────────┘
```

---

## 2. System Architecture

### Overall Architecture

The system consists of four main modules:

1. **Knowledge Graph Pipeline** (`kg2.py`): Parses PDFs, extracts entities/relationships, builds Neo4j graph
2. **Summarization Pipeline** (`summarize.py`): Generates field-by-field summaries using GraphRAG
3. **QA Engine** (`qa_engine.py`): Hybrid RAG question-answering with faithfulness verification
4. **Benchmarking** (`cognisynth_Benchmark.py`, `eval_summary.py`): Evaluates system quality

### Data Flow

1. **PDF → Docling**: Document parsed into DoclingDocument with OCRM
2. **DoclingDocument → HybridChunker**: Split into semantic chunks preserving table/heading structure
3. **Chunks → Dual Extraction**:
   - GLiNER: Fast NER for entity detection
   - Groq NER: Slow but relationship-rich extraction
4. **Entities/Relations → Neo4j**: Graph storage with vector embeddings
5. **Summarization**: Vector search + Graph queries + Figure evidence → LLM → Summary
6. **QA**: HyDE query expansion + Graph neighborhood + Reranking → Answer

### Pipeline Execution Sequence

```
1. kg2.py build_knowledge_graph(pdf_path)
   - Clears Neo4j if fresh run
   - Converts PDF via Docling
   - Chunks via HybridChunker
   - For each chunk:
     a. GLiNER entity extraction
     b. Groq NER with relationships
     c. Merge, normalize, deduplicate
     d. Ingest to Neo4j
   - Build section hierarchy
   - Store chunk embeddings

2. summarize.py main()
   - Load figures from Neo4j (from richy.py pre-processing)
   - For each field (abstract, problem, approach, etc.):
     a. Vector search via embeddings
     b. Section-based retrieval for tables
     c. KV chunk injection for evaluation
     d. Cross-encoder reranking
     e. Graph context query
     f. Figure evidence injection
     g. LLM field answer
   - Synthesis to "At a Glance" summary

3. qa_engine.py answer_question()
   - Load paper summary
   - Extract query entities
   - Graph neighborhood retrieval (2 hops)
   - HyDE hypothetical answer → vector
   - Rerank + fallback guard
   - Context assembly
   - LLM answer generation
   - Faithfulness verification

4. eval_summary.py main()
   - Derive fact checklist from ground truth
   - Stage 1: Semantic hit rate per field
   - Stage 2: Faithfulness LLM judge
   - Stage 3: Information density judge
   - Stage 4: Structural adherence regex
   - Composite score: 0.35×hit + 0.35×faith + 0.20×density + 0.10×structure
```

### Internal Dependencies

- **Neo4j**: Primary storage for entities, relationships, chunks, sections
- **Groq API**: NER extraction, summarization, QA generation
- **GLiNER**: Fast local NER (fallback if unavailable)
- **Docling**: PDF parsing with OCRM
- **sentence-transformers**: BGE-M3 embeddings
- **Cross-encoder**: BGE-reranker-v2-m3 for relevance scoring

---

## 3. File-by-File Breakdown

### kg2.py — Knowledge Graph Pipeline

**Purpose**: Build a Neo4j knowledge graph from academic papers with entity extraction, relationship detection, and chunk embeddings.

**Key Functions**:

- `load_document()`: Docling JSON cache or fresh PDF conversion
- `chunk_document()`: HybridChunker with token-boundary splitting, table repeat headers
- `gliner_extract()`: Local GLiNER NER (threshold 0.4)
- `groq_extract_entities()`: Groq NER with rate limiting (30K TPM, 30 RPM Llama 4 Scout)
- `clean_entity()`: Validate type, normalize name, blacklist filter
- `merge_entity_sources()`: Combine GLiNER + Groq with canonical deduplication
- `ingest_*()`: Neo4j batch ingestion via UNWIND
- `embed_chunks()`: BGE-M3 embeddings stored in Neo4j vector index
- `build_knowledge_graph()`: Main pipeline orchestrator
- `print_graph_stats()`: Entity counts, type breakdown, hub entities

**Configuration**:

- Rate limiter: 27K effective TPM (90% safety), ~1s between calls
- Allowed entity types: MODEL, DATASET, METRIC, TECHNIQUE, TASK, ARCHITECTURE_COMPONENT
- Canonical registry: First-seen name wins, cleared per run
- Blacklists: UNIVERSAL_BLACKLIST (generic terms), \_RUNTIME_BLACKLIST (paper-specific)

**Input**: PDF file path
**Output**: Neo4j graph with Entity/Chunk/Section nodes and MENTIONS/relationship edges

---

### summarize.py — GraphRAG Summarization Pipeline

**Purpose**: Generate structured, field-by-field paper summaries using hybrid retrieval (vector + graph + figures).

**Key Functions**:

- `init_clients()`: Groq, Neo4j driver, SentenceTransformer, CrossEncoder
- `vector_search()`: Embedding search with section exclusion + [KV:] tag stripping
- `rerank_field_chunks()`: Cross-encoder scoring against field question
- `build_section_map()`: Runtime classification of sections to fields via regex patterns
- `get_section_chunks()`: Section-based retrieval for tabular data
- `get_kv_chunks()`: Key-value extraction for numerical evaluation data
- `get_graph_context()`: Field-specific Cypher queries against Neo4j
- `load_figures_from_neo4j()`: Parse VLM-generated figure descriptions by type
- `get_figure_evidence()`: Safety-net filtered figure injection per field
- `answer_field()`: LLM call with field-specific token limits
- `synthesize()`: 4-sentence "At a Glance" summary generation
- `main()`: Orchestrates all phases

**Retrieval Strategy**:

- Vector search → 15 candidates → cross-encoder rerank to 5
- Section-based supplement for evaluation/comparisons/architecture fields
- KV injection for structured numbers
- Graph Cypher for architecture (HAS_COMPONENT), evaluation (SCORED_ON), training (TRAINED_ON)
- Figure evidence: RESULT_CHART blocked from approach/architecture (safety net)

**Key Variables**:

- `FIELD_MAX_TOKENS_OVERRIDE`: 1500 for evaluation/comparisons/contributions/results
- `EXCLUDED_SECTIONS`: Contents, Table of Contents, References, Bibliography
- `FIELD_SECTION_EXCLUSIONS`: Discussion/Conclusion blocked from evaluation/comparisons
- `TOP_K_CHUNKS = 5`, `MAX_CHUNK_CHARS = 3000`

**Input**: Neo4j graph + figures (from richy.py)
**Output**: Markdown summary file + `summary_debug.json`

---

### qa_engine.py — Question Answering Engine

**Purpose**: Hybrid RAG QA with HyDE query expansion, multi-hop graph retrieval, cross-encoder reranking, and faithfulness verification.

**Key Classes**:

- `QAEngine`: Singleton managing clients and retrieval pipeline

**Key Methods**:

- `extract_query_entities()`: LLM extraction of ML entities from query
- `get_graph_neighborhood()`: 2-hop Cypher traversal with CONTAINS fuzzy matching
- `vector_search()`: Standard embedding search
- `vector_search_with_vector()`: Pre-computed vector search
- `rerank_chunks()`: Cross-encoder scoring
- `generate_hyde_vector()`: Hypothetical answer → embedding (falls back to query embedding)
- `verify_faithfulness()`: Citation-based claim verification against source chunks
- `answer_question()`: Main pipeline orchestrator with 3 return modes

**Key Features**:

- HyDE fallback guard: If top rerank score < 0.1, retry with raw query
- Citation format: `[Ref: chunk_XXXXX]`
- Context assembly: Summary → Graph triples → Chunks with [KV:] stripped
- Faithfulness: Extracts citations, verifies each claim against source

**Input**: User question
**Output**: Answer string or dict with answer, verified status, flags, context, metadata

---

### cognisynth_Benchmark.py — Ragas Benchmark Evaluation

**Purpose**: Compare CogniSynth against black-box LLMs (GPT, Gemini) using Ragas metrics.

**Key Components**:

- `TestCase` dataclass: Question, reference answer, contexts per system, responses
- `SYSTEMS`: CogniSynth, GPT (Pro/Free), Gemini (Pro/Flash)
- `build_metrics()`: Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference, LLMContextRecall
- `score_single()`: Async scoring of one (system, question) pair
- `run_evaluation()`: Concurrent evaluation of all test cases
- `build_report()`: Per-system average comparison table
- `build_per_question_report()`: Granular (system × question) breakdown

**Metrics**:

- Faithfulness: Claims grounded in retrieved context?
- Response Relevancy: Does response answer the question?
- Context Precision: Are retrieved chunks relevant?
- Context Recall: Does context cover ground truth?

**Test Cases**: 7 questions targeting VLM tabular extraction, GraphRAG architecture retrieval, synthesis edge cases

**Input**: Mock responses (or real API calls in production)
**Output**: CSV comparison + JSON raw scores

---

### eval_summary.py — Multi-Axis Summary Evaluation

**Purpose**: Evaluate summaries against ground truth across 4 axes with composite scoring.

**Evaluation Stages**:

1. **Semantic Hit Rate (35%)**: LLM verifies each ground truth fact is expressed
2. **Faithfulness (35%)**: GT-anchored 1-5 score by LLM judge
3. **Information Density (20%)**: Useful content per word, LLM judge 1-5
4. **Structural Adherence (10%)**: Regex detection of 11 expected field headers

**Field Weights for Hit Rate**:

- Architecture: 30%
- Methodology: 20%
- Comparisons: 20%
- Training: 15%
- Datasets: 15%

**Key Functions**:

- `derive_fact_checklist()`: Extracts verifiable claims from ground_truth_joint.json
- `score_hit_rate_semantic()`: Per-field LLM verification with JSON parsing
- `score_faithfulness()`: GT-anchored judge prompt
- `score_information_density()`: Efficiency evaluation
- `score_structure()`: Regex-based header detection
- `compute_composite()`: Weighted score combination

**Input**: Ground truth JSON + summary files
**Output**: eval_results.json with per-system scores + leaderboard

---

## 4. Knowledge Graph Pipeline

### Knowledge Graph Generation Process

```
PDF → DoclingDocument → HybridChunker → Chunks
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              GLiNER NER           Groq NER + Rel          Neo4j Ingest
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          ▼
                                    Merged Entities
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              Entity Nodes          Relationship Edges     Chunk Nodes
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              Section Nodes     Section-CONTAINS-Chunk   Vector Embeddings
```

### Entity Extraction

**Allowed Types**: MODEL, DATASET, METRIC, TECHNIQUE, TASK, ARCHITECTURE_COMPONENT

**GLiNER** (fast, local):

- Threshold: 0.4
- Labels: Same as ALLOWED_TYPES
- Source tag: "gliner"

**Groq NER** (slow, relationship-rich):

- Model: meta-llama/llama-4-scout-17b-16e-instruct
- Rate limiting: Token-aware TPM + call-aware RPM
- Validates response format before accepting
- Retries: 3 attempts with JSON/rate-limit handling

### Canonical Name Deduplication

```python
def normalise_for_dedup(name: str) -> str:
    # "DeepSeek-OCR" → "deepseekocr"
    # "DeepSeek OCR" → "deepseekocr"  (same key)
    # "GPT-3" → "gpt3"
    # "GPT-4" → "gpt4"  (different key, digits preserved)
```

First-seen variant becomes canonical; subsequent variants map to it.

### Relationship Extraction

**Explicit Relationships Only** (from Groq NER):

- MODEL → trained_on → DATASET
- MODEL → achieves / evaluated_by → METRIC
- MODEL → uses → TECHNIQUE
- MODEL → performs → TASK
- MODEL → has_component → ARCHITECTURE_COMPONENT

**Relationship Type Cleaning**: Uppercase + underscore substitution (e.g., "trained on" → "TRAINED_ON")

### Blacklisting

**Universal Blacklist** (never valid):

- Generic ML terms: model, dataset, encoder, layer, training, inference
- Size qualifiers: tiny, small, large, base, mini
- Document references: figure, table, section, step 1
- Single characters: e, n, k, m, s, x, a, b

**Runtime Blacklist** (seed + paper-specific additions):

- Libraries: fitz, pymupdf, torch, transformers
- Hardware: a100, v100, h100, gpu, cpu, tpu
- Hallucinations: "three different models", "large language model"

**Regex Patterns**:

- `^figure\s*\d+`, `^table\s*\d+`, `^step\s*\d+`
- `^\d+\.?\d*[xX×]?$` (bare numbers)
- `^[a-zA-Z]$` (single chars)
- `^https?://`, `arxiv`

### Graph Construction Logic

1. **Clear graph** on fresh run (skip if resuming from checkpoint)
2. **Setup constraints/indexes**: Entity.name UNIQUE, Chunk.id UNIQUE, vector index (1024 dim, cosine)
3. **Per-chunk ingestion**:
   - MERGE Chunk node
   - UNWIND entities → MERGE Entity → MERGE (Chunk)-[:MENTIONS]->(Entity)
   - UNWIND relationships → MATCH a,b → MERGE (a)-[r:type]->(b)
4. **Section hierarchy**: MERGE Section → UNWIND chunk IDs → MERGE (Section)-[:CONTAINS]->(Chunk)
5. **Embeddings**: Encode all chunks → UNWIND batch → SET c.embedding

### Storage and Retrieval

**Neo4j Schema**:

- `(:Entity {name, type, description})`
- `(:Chunk {id, text, section, page, type, ref, embedding})`
- `(:Section {name})`
- `(:Chunk)-[:MENTIONS]->(:Entity)`
- `(:Entity)-[:relationship_type]->(:Entity)`
- `(:Section)-[:CONTAINS]->(:Chunk)`
- Vector index on `Chunk.embedding` (1024 dimensions, cosine similarity)

### Graph Querying Approach

**Field-Specific Cypher Patterns**:

| Field        | Cypher Pattern                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| architecture | `MATCH (m:Entity {type:'MODEL'})-[r:HAS_COMPONENT]->(c:Entity) WHERE m.name CONTAINS $primary`                  |
| evaluation   | `MATCH (m:Entity)-[ra:SCORED_ON]->(met:Entity {type:'METRIC'})`                                                 |
| training     | `MATCH (m:Entity)-[r:TRAINED_ON]->(d:Entity {type:'DATASET'}) WHERE m.name CONTAINS $primary`                   |
| approach     | `MATCH (m:Entity {name:$primary})-[r:USES]->(e:Entity) WHERE e.type IN ['TECHNIQUE', 'ARCHITECTURE_COMPONENT']` |
| comparisons  | Shared dataset scoring + explicit OUTPERFORMS/BEATS edges                                                       |
| implications | Conclusion/Discussion section chunks (text, not relationships)                                                  |

**Entity Neighborhood**:

```cypher
MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($ent)
MATCH (e)-[r]-(neighbor:Entity)
RETURN e.name, type(r), neighbor.name

-- 2-hop limited
MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($ent)
MATCH (e)-[]-(n1:Entity)-[r]-(n2:Entity)
WHERE n2.name <> e.name
RETURN n1.name, type(r), n2.name
```

---

## 5. Summarization Pipeline

### Summarization Methodology

**Template-Guided + Graph-Enriched + Figure-Injected** strategy:

1. **Template**: Pre-defined field questions (abstract, problem, approach, architecture, training, evaluation, results, comparisons, contributions, implications, conclusion)
2. **Graph Enrichment**: Field-specific Cypher queries add relational context
3. **Figure Injection**: VLM-generated descriptions from richy.py

### Chunking Strategy

**HybridChunker** (from docling_core):

- Token boundary-aware text splitting (semchunk)
- Table splitting with `repeat_table_header=True`
- Heading hierarchy preservation via `headings stack`
- `always_emit_headings=True`
- `merge_peers=True`
- Max tokens: 1500 (configurable)

**Section Filtering**: Skips "References", "Bibliography", "Acknowledgements", "Appendix", "Table of Contents"

### Prompting Strategy

**Per-Field Answer** (`FIELD_SYSTEM_PROMPT`):

```
You are a precise scientific summarizer.
Answer the question using ONLY the provided context.
Be specific — include model names, metric values, dataset names, and numbers where available.
Do NOT hallucinate or add information not in the context.
Write 3-5 sentences maximum. No bullet points.
```

**Groq NER Prompt** (`NER_USER_TEMPLATE`):

```
Extract named entities and their relationships from this ML research text.
STRICT RULES:
1. Entity types MUST be one of: MODEL, DATASET, METRIC, TECHNIQUE, TASK, ARCHITECTURE_COMPONENT
2. DO NOT extract: generic words, figure/table references, numbers alone, single characters
3. Relationships (explicit only): MODEL→trained_on/evaluated_on→DATASET, MODEL→achieves→METRIC, etc.
```

**Synthesis Prompt** (`SYNTHESIS_SYSTEM_PROMPT`):

```
Generate EXACTLY these 4 lines and nothing else:
**Core Claim:** <one sentence>
**Key Method:** <one sentence>
**Best Result:** <one sentence>
**Why It Matters:** <one sentence>
```

### LLM Usage

| Module       | Model                 | Purpose                   | Rate Limit          |
| ------------ | --------------------- | ------------------------- | ------------------- |
| kg2.py NER   | Llama 4 Scout 17B 16E | Entity extraction         | 30K TPM, 30 RPM     |
| summarize.py | gpt-oss-120b          | Field answers + synthesis | 8K TPM (85% safety) |
| qa_engine.py | Llama 4 Scout 17B 16E | Answer generation         | 30K TPM             |

### Context Handling

1. **Vector Search**: 15 candidates → cross-encoder rerank to 5
2. **Section Supplement**: For tabular fields, additional chunks from matching sections
3. **KV Injection**: Evaluation field gets additional key-value extracted chunks
4. **[KV:] Stripping**: All `[KV: ...]` tags removed from chunk text before LLM input
5. **Figure Cap**: Max 2 figures per field to prevent token explosion

### Output Generation

1. **Field Answers**: 11 fields × LLM call → stored in `field_answers` dict
2. **Synthesis**: 4-line "At a Glance" summary from field answers
3. **Full Output**: Synthesis + field-by-field breakdown in markdown
4. **Debug Output**: `summary_debug.json` with full context per field

### Evaluation Approach

See [Benchmarking and Evaluation](#7-benchmarking-and-evaluation) section for details on eval_summary.py methodology.

---

## 6. QA Engine

### Question Answering Workflow

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. Load paper summary (global context)  │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    ▼                           ▼
┌───────────────┐       ┌───────────────┐
│ 2. Extract    │       │ 3. Graph      │
│ query entities│       │ neighborhood  │
│ (LLM)         │       │ (2-hop Cypher)│
└───────┬───────┘       └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────┐
│ 4. HyDE vector generation               │
│    Hypothetical answer → embed          │
└─────────────────┬───────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 5. Vector search with HyDE vector      │
└─────────────────┬───────────────────────┘
                    │
    ┌───────────────┴───────────────┐
    ▼                               ▼
┌───────────────┐             ┌───────────────┐
│ 6a. Rerank    │             │ 6b. Fallback  │
│ cross-encoder │             │ if score<0.1 │
│ top 8         │             │ raw query     │
└───────┬───────┘             └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────┐
│ 7. Context assembly                     │
│    Summary + Graph + Chunks            │
└─────────────────┬───────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 8. LLM answer generation                │
│    [Ref: chunk_XXXXX] citations        │
└─────────────────┬───────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 9. Faithfulness verification           │
│    Verify claims against source chunks │
└─────────────────────────────────────────┘
```

### Retrieval Process

1. **Entity Extraction**: LLM extracts ML entities from query (comma-separated list)
2. **Graph Neighborhood**: 2-hop traversal with CONTAINS fuzzy matching
3. **HyDE Vector**: Hypothetical answer paragraph → BGE-M3 embedding
4. **Vector Search**: Pre-computed vector → Neo4j vector index query
5. **Reranking**: Cross-encoder scores (query, chunk) pairs

### Context Assembly

```python
context = []
if summary_text:
    context.append(f"### PAPER SUMMARY\n{summary_text[:1500]}")
if graph_triples:
    context.append("### KNOWLEDGE GRAPH DATA\n" + "\n".join(graph_triples[:20]))
context.append("### RELEVANT PAPER CHUNKS")
for c in chunks:
    text = re.sub(r'\[KV:[^\]]+\]', '', c['text']).strip()
    context.append(f"[{c['section']} | Ref: {chunk_id}] {text[:2500]}")
```

### Ranking/Relevance Mechanisms

1. **Cosine Similarity**: Initial vector search ranking
2. **Cross-Encoder Reranking**: `(query, chunk)` → relevance score
3. **HyDE Fallback Guard**: If top cross-encoder score < 0.1, retry with raw query

### Prompt Engineering

```
You are a research assistant answering questions about a technical paper.
Use the provided SUMMARY, KNOWLEDGE GRAPH, and PAPER CHUNKS to answer the user's question.

RULES:
1. Be technically precise, professional, and CONCISE.
2. SYNTHESIZE information from all context sources.
3. AVOID REPETITION.
4. If the answer is truly not in the context, say so once.
5. ALWAYS cite your sources using [Ref: chunk_XXXXX] format.
```

### Final Answer Generation

- Model: Llama 4 Scout 17B 16E
- Temperature: 0.3
- Max tokens: 1024
- Citation format: `[Ref: chunk_XXXXX]`

### Faithfulness Verification

```python
# Extract cited sentences
citation_pattern = r'([^.!?]*\[Ref:\s*(chunk_\w+)\][^.!?]*[.!?])'
cited_sentences = citation_pattern.findall(answer)

# Batch verification prompt
"For each numbered claim below, decide if the SOURCE TEXT supports it.
Return ONLY JSON: [{\"id\": N, \"verdict\": \"SUPPORTED\"|\"UNSUPPORTED\", \"reason\": \"...\"}]"
```

---

## 7. Benchmarking and Evaluation

### Benchmark Methodology

#### CogniSynth Benchmark (cognisynth_Benchmark.py)

**Ragas Framework** for evaluation metrics:

- Faithfulness: LLM judge scores whether claims are in context
- Response Relevancy: LLM judge scores whether response addresses question
- Context Precision: Per-chunk relevance to question
- Context Recall: Whether context covers ground truth

**Test Document**: DeepSeek-OCR paper (context optical compression)

**Test Cases (7 questions)**:
| ID | Category | Question Type |
|----|----------|---------------|
| Q1 | Tabular & Chart Data | VLM + Docling extraction |
| Q2 | Compression Trajectory | Chart data degradation |
| Q3 | Architecture | GraphRAG entity relationships |
| Q4 | Abstract Concepts | GraphRAG synthesis |
| Q5 | Real-World Limitations | Synthesis edge cases |
| Q6 | Operational Modes | Synthesis |
| Q7 | Vision Token Comparison | Figure extraction |

**Systems Compared**: CogniSynth, GPT(Pro/Free), Gemini (Pro/Flash)

#### Summary Evaluation (eval_summary.py)

**4-Axis Evaluation**:

| Axis                 | Weight | Method                          | Scoring                 |
| -------------------- | ------ | ------------------------------- | ----------------------- |
| Factual Hit Rate     | 35%    | LLM semantic matching per field | Per-field weighted rate |
| Faithfulness         | 35%    | GT-anchored LLM judge           | 1-5 normalized          |
| Information Density  | 20%    | LLM judge: useful content/word  | 1-5 normalized          |
| Structural Adherence | 10%    | Regex header detection          | 0-11 fields             |

**Field Weights for Hit Rate**:

- Architecture: 30%
- Methodology: 20%
- Comparisons: 20%
- Training: 15%
- Datasets: 15%

### Evaluation Results Analysis

**Leaderboard** (from eval_results.json):

| Rank | System         | Composite  | Hit Rate | Faithfulness | Density | Structure |
| ---- | -------------- | ---------- | -------- | ------------ | ------- | --------- |
| 1    | GPT_Std        | **94.29%** | 83.67%   | 5/5          | 5/5     | 11/11     |
| 2    | GPT_OSS_KG3    | **91.13%** | 74.64%   | 5/5          | 5/5     | 11/11     |
| 3    | GPT_OSS_KG3_V2 | **85.82%** | 79.49%   | 4/5          | 5/5     | 11/11     |
| 4    | Gemini_Pro     | **84.76%** | 76.46%   | 4/5          | 5/5     | 11/11     |
| 5    | GPT_Pro        | **83.15%** | 83.28%   | 4/5          | 4/5     | 11/11     |
| 6    | Paper_Summary  | **82.58%** | 70.24%   | 4/5          | 5/5     | 11/11     |
| 7    | CogniSynth_V2  | **82.46%** | 81.31%   | 4/5          | 4/5     | 11/11     |
| 8    | Gemini_Std     | **79.98%** | 82.80%   | 3/5          | 5/5     | 11/11     |
| 9    | Gemini_Flash   | **61.95%** | 50.49%   | 3/5          | 4/5     | 8/11      |

### Key Findings from Evaluation

**Strengths**:

1. **GPT_Std** achieves highest composite (94.29%) with perfect faithfulness and density
2. **CogniSynth_V2** performs competitively (82.46%) despite simpler architecture
3. **GraphRAG systems** (GPT_OSS_KG3, CogniSynth) maintain high structural adherence (11/11)
4. **Architecture field** shows highest hit rates across most systems (70-100%)

**Weaknesses**:

1. **Gemini_Flash** suffers from poor Training field recall (0%) and missing structural fields
2. **Methodology field** is weakest across all systems (45-82% hit rates)
3. **Fabricated metrics**: Gemini_Std and Gemini_Flash introduce unsupported numbers
4. **Training details** frequently missing or incorrect in lower-ranked systems

**CogniSynth_V2 Specific Analysis**:

- Strengths: Perfect structure (11/11), strong Training (88.89%), excellent Comparisons (100%)
- Weaknesses: Methodology only 63.64% hit rate, minor fabricated compression ratio claims
- Faithfulness: Score 4/5 — core architecture accurate, minor unsupported claims

### Interpretation

The evaluation demonstrates that:

1. **Faithfulness + Density matter more than raw hit rate**: GPT_Std leads despite not having highest hit rate
2. **GraphRAG provides consistency**: CogniSynth_V2 and GPT_OSS_KG3 show stable, high faithfulness
3. **Structural adherence is necessary but not sufficient**: Gemini_Flash has 8/11 but ranks last
4. **LLM-judged metrics reveal quality gaps**: Human-judged density/faithfulness correlate better with actual usefulness than pure fact-counting

---

## 8. Technologies and Dependencies

### Libraries/Frameworks

| Library               | Version | Purpose                                         |
| --------------------- | ------- | ----------------------------------------------- |
| groq                  | latest  | Groq API client for NER/summarization/QA        |
| neo4j                 | latest  | Neo4j Python driver for graph storage           |
| docling               | latest  | PDF parsing with OCRM                           |
| docling_core          | latest  | DoclingDocument types, HybridChunker            |
| sentence-transformers | latest  | BGE-M3 embeddings, cross-encoder reranker       |
| gliner                | latest  | Local NER (optional, falls back if unavailable) |
| ragas                 | latest  | Benchmark evaluation metrics                    |
| langchain-groq        | latest  | Ragas LLM wrapper                               |
| langchain-huggingface | latest  | Ragas embeddings wrapper                        |
| python-dotenv         | latest  | Environment variable loading                    |

### External APIs/Models

| Service     | Model                                     | Purpose          | Limits          |
| ----------- | ----------------------------------------- | ---------------- | --------------- |
| Groq        | meta-llama/llama-4-scout-17b-16e-instruct | NER, QA          | 30K TPM, 30 RPM |
| Groq        | openai/gpt-oss-120b                       | Summarization    | 8K TPM          |
| Groq        | qwen/qwen3-32b                            | Evaluation judge | -               |
| HuggingFace | BAAI/bge-m3                               | Embeddings       | -               |
| HuggingFace | BAAI/bge-reranker-v2-m3                   | Reranking        | -               |
| HuggingFace | ./models/gliner_small                     | Local NER        | Offline         |

### Environment Requirements

- Python 3.10+
- Neo4j Desktop or Aura instance
- Groq API key
- 8GB+ RAM for Docling PDF processing
- GPU optional (for sentence-transformers)

### Installation

```bash
cd graphrag-fyp
pip install groq neo4j docling docling_core sentence-transformers gliner ragas langchain-groq langchain-huggingface python-dotenv
```

### Configuration (.env)

```bash
GROQ_API_KEY=your_groq_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

---

## 9. Execution Guide

### Setup Instructions

1. **Neo4j Setup**:

   ```bash
   # Neo4j Desktop: Create local database on port 7687
   # Or Aura: Get connection URI from dashboard
   ```

2. **Environment**:

   ```bash
   cd graphrag-fyp
   cp .env.example .env  # Fill in GROQ_API_KEY, Neo4j credentials
   ```

3. **GLiNER Model** (optional):
   ```bash
   # Models will download on first use if not present locally
   mkdir -p models
   ```

### Running the Pipeline

#### 1. Knowledge Graph Build

```bash
# Process a paper
uv run kg2.py data/deepseek.pdf

# Resume from checkpoint (if interrupted)
uv run kg2.py data/deepseek.pdf

# View graph stats
uv run kg2.py  # No args prints help
```

**Expected Output**:

```
INFO: Loading document …
INFO: HybridChunker produced X chunks
INFO: [1/100] chunk_00000 | type=text | section=Introduction
INFO: Entity stats: 150 raw → 45 clean (105 rejected)
INFO: ✅ Knowledge graph complete!
📊 Graph Statistics:
   Entity              : 45
   Chunk               : 100
   Relationships       : 78
```

#### 2. Summarization

```bash
# Full pipeline
uv run summarize.py

# Single field debug
uv run summarize.py --field evaluation

# Skip graph enrichment
uv run summarize.py --no-graph

# Skip figure evidence
uv run summarize.py --no-figures

# Skip synthesis
uv run summarize.py --no-synth
```

**Expected Output**:

```
📄 GraphRAG Paper Summarizer
   Graph enrichment : ✅
   Figure evidence  : ✅

📋 Field: architecture
   Chunks retrieved : 15
   Section chunks   : 5 merged
   Chunks after rerank: 5
   Graph triples    : 12
   Figures injected : 2
   ✅ Answer: The DeepEncoder consists of three stages...
```

**Output Files**:

- `gpt_oss_kg3_summary_v2.md` — Final summary
- `summary_debug.json` — Full context for debugging

#### 3. QA Engine

```bash
# Interactive query
uv run qa_engine.py "What is the DeepEncoder architecture?"

# Programmatic usage
python -c "
from qa_engine import answer_question
result = answer_question('How does Gundam mode work?', return_full=True)
print(result['answer'])
print('Verified:', result['verified'])
"
```

#### 4. Evaluation

```bash
# Full evaluation
uv run eval_summary.py --gt ground_truth_joint.json

# Custom output
uv run eval_summary.py --gt ground_truth_joint.json --output my_eval.json
```

**Expected Output**:

```
📋 Loaded ground truth from ground_truth_joint.json
   Derived 37 facts across 5 fields

🔍 Evaluating: CogniSynth_V2
   Hit Rate (weighted): 81.31%
   Hit Rate (raw):      29/37
   Faithfulness:        4/5
   Info Density:        4/5
   Structure:           11/11 fields
   ✨ Composite Score:   82.46%

==============================================================
System           Composite   Hit Rate   Faithful   Density   Structure
==============================================================
1. GPT_Std          94.29%     83.67%       5/5       5/5      11/11
2. GPT_OSS_KG3      91.13%     74.64%       5/5       5/5      11/11
...
```

---

## 10. Implementation Details

### Design Decisions

#### Rate Limiting Architecture

**Token-Aware TPM + Call-Aware RPM**:

```python
# TPM: Rolling 60-second window
_token_log: list[tuple[float, int]] = []  # (timestamp, tokens)
used = sum(t for ts, t in _token_log if ts > now - 60)

# RPM: Minimum interval between calls
_MIN_INTERVAL = 60.0 / (30 * 0.85)  # ~1s safety margin
```

**Why**: Groq Llama 4 Scout has 30K TPM / 30 RPM limits. Token tracking prevents mid-window rejections better than simple time-based throttling.

#### Canonical Name Registry

**First-Seen Wins** with normalized deduplication:

- "DeepSeek-OCR" and "DeepSeek OCR" → same canonical name
- "GPT-3" and "GPT-4" → different (digits preserved)

**Why**: Academic papers use inconsistent naming. Canonical registry ensures entity deduplication without losing specificity.

#### HybridChunker for Document Parsing

**Why not simple chunking**:

- Tables need header repetition across splits
- Semantic chunking respects sentence boundaries
- Heading hierarchy preserved for section-based retrieval

#### Cross-Encoder Reranking

**Why**: Cosine similarity in embedding space doesn't correlate with relevance to specific query intent. Cross-encoder scores `(query, document)` pairs directly.

**Procedure**: 15 candidates → rerank → top 5. Capped at 2 figures per field to prevent context flooding.

#### HyDE Query Expansion

**Hypothetical Answer → Embedding**:

1. LLM writes plausible answer paragraph
2. Embed paragraph with same model as chunks
3. Vector search with this embedding

**Why**: "Good answers look similar to good contexts." HyDE captures what a relevant response would contain, improving recall.

**Fallback Guard**: If rerank score < 0.1, raw query used instead. Prevents bad HyDE vectors from degrading results.

### Important Algorithms

#### Entity Cleaning Pipeline

```
Raw Entity → Type Validation → Name Normalization → Blacklist Filter → Type Override → Canonical Lookup
     │              │                  │                  │              │               │
     ▼              ▼                  ▼                  ▼              ▼               ▼
  dict/str    in ALLOWED_TYPES?   normalise_for_dedup   is_blacklisted?  ENTITY_TYPE_   get_canonical()
                                               _OVERRIDES
```

#### Canonical Deduplication

```python
_canonical_registry: dict[str, str] = {}  # normalized → canonical

def get_canonical(name):
    key = normalise_for_dedup(name)
    if key not in _canonical_registry:
        _canonical_registry[key] = name  # first seen wins
    return _canonical_registry[key]
```

#### Section Map Building

```python
# Runtime: Scan Neo4j sections → match against FIELD_TO_SECTION_PATTERNS
for section_name in all_sections:
    for field, patterns in FIELD_TO_SECTION_PATTERNS.items():
        if any(re.search(p, section_name.lower()):
            section_map[field].append(section_name)
```

### Error Handling

| Error Type               | Handling                           |
| ------------------------ | ---------------------------------- |
| Groq rate limit (429)    | Parse wait time, sleep + retry     |
| JSON parse failure       | Retry full prompt (up to 3×)       |
| GLiNER unavailable       | Continue with Groq-only extraction |
| Neo4j connection         | `verify_connectivity()` at init    |
| Embedding import fail    | Log warning, skip embedding        |
| Short chunk (<150 chars) | Skip NER, save context only        |

### Scalability Considerations

1. **Checkpointing**: `kg2_checkpoint.json` allows resume on interruption
2. **Batch Ingestion**: UNWIND for bulk entity/relationship loading
3. **Token Tracking**: Rolling window prevents API quota exhaustion on long papers
4. **Checkpoint-per-chunk**: Saves after each chunk for fine-grained resume

### Limitations

1. **GLiNER required for best results**: Falls back to Groq-only if unavailable
2. **PDF only**: No Word/HTML support
3. **English-focused**: NER prompts optimized for ML papers
4. **No streaming**: Full document processed before any output
5. **Checkpoint file race condition**: Concurrent runs could corrupt checkpoint

---

## 11. Research and Technical Insights

### Why These Approaches Were Chosen

#### GraphRAG over Simple Vector RAG

**Research shows**: Relational facts ("Model X uses Technique Y") are not recoverable from chunk similarity alone. GraphRAG captures:

- Entity co-occurrence patterns
- Relationship types (trained_on, achieves, uses)
- Multi-hop connections (A→B→C)

**CogniSynth insight**: Field-specific Cypher queries extract exactly the context needed for each summary dimension.

#### HybridChunker over Simple Splitting

**Problem**: Academic papers have:

- Multi-page tables that need header repetition
- Heading hierarchies that indicate section roles
- Mixed content (text + formulas + tables)

**Solution**: HybridChunker handles all three, enabling section-based retrieval and table preservation.

#### Dual NER (GLiNER + Groq)

**Trade-off**:

- GLiNER: Fast, local, no rate limits, but no relationships
- Groq: Slow, rate-limited, but extracts relationships with entities

**CogniSynth insight**: Merge both — Groq provides relationships, GLiNER fills coverage gaps at low cost.

#### Cross-Encoder Reranking

**Why not cosine alone**: Embedding models optimize for semantic similarity, not query-document relevance. Cross-encoder sees both simultaneously.

**Cost**: ~2× encode time but significantly better ranking for QA tasks.

### Trade-offs

| Decision             | Trade-off                                     |
| -------------------- | --------------------------------------------- |
| Canonical registry   | Memory usage vs. entity deduplication quality |
| HyDE                 | Extra LLM call vs. recall improvement         |
| Figure cap (2/field) | Completeness vs. token budget                 |
| Checkpoint per chunk | Safety vs. I/O overhead                       |
| BGE-M3 embeddings    | Quality vs. vector dimension (1024)           |

### Potential Improvements

1. **Streaming pipeline**: Output chunks as processed, not all-at-end
2. **Concurrent Neo4j writes**: asyncio for ingestion parallelism
3. **Adaptive chunk sizing**: Larger chunks for dense sections
4. **Multi-paper graphs**: Allow entities to link across papers
5. **Figure-grounding**: Link figure citations to specific sections
6. **Evaluation automation**: Run cognisynth_Benchmark.py with real API calls

### Future Enhancements

1. **Ragas integration in main pipeline**: Real-time faithfulness scores
2. **Interactive QA mode**: Follow-up question tracking
3. **Paper comparison mode**: Cross-paper entity/relationship overlap
4. **Knowledge graph updates**: Incremental additions, not full rebuild
5. **Citation graph**: Track which paper cites which

### Research Relevance

This project demonstrates:

1. **GraphRAG viability** for academic paper understanding
2. **Hybrid retrieval** (vector + graph + figure) superiority over single-method
3. **Faithfulness verification** as critical component for trust
4. **Cross-encoder reranking** importance for precision-sensitive tasks
5. **Evaluation methodology** combining automatic metrics with LLM judgment

---

## 12. Project Context File

### System Summary

CogniSynth is a GraphRAG + VLM pipeline for academic paper understanding. It processes PDFs through document parsing (Docling), entity extraction (GLiNER + Groq NER), knowledge graph construction (Neo4j), and multi-axis summarization with QA capabilities.

### Module Summary

| Module        | File                      | Purpose                                                    |
| ------------- | ------------------------- | ---------------------------------------------------------- |
| KG Pipeline   | `kg2.py`                  | PDF → Neo4j graph with entities, relationships, embeddings |
| Summarization | `summarize.py`            | Neo4j + figures → field-by-field markdown summary          |
| QA Engine     | `qa_engine.py`            | Question → answer with graph context + verification        |
| Benchmark     | `cognisynth_Benchmark.py` | Ragas evaluation vs. black-box LLMs                        |
| Evaluation    | `eval_summary.py`         | Ground-truth based summary quality scoring                 |

### Key Terminology

| Term                   | Definition                                                       |
| ---------------------- | ---------------------------------------------------------------- |
| **GraphRAG**           | Retrieval Augmented Generation using knowledge graph context     |
| **HybridChunker**      | Docling chunker handling tables, headings, token boundaries      |
| **Canonical Registry** | First-seen entity name mapping for deduplication                 |
| **HyDE**               | Hypothetical Document Embeddings — LLM writes answer, embed that |
| **Cross-Encoder**      | Neural reranker scoring (query, document) pairs                  |
| **Faithfulness**       | Whether generated claims are supported by source context         |
| **Hit Rate**           | Ground truth facts present in summary (semantic match)           |

### Workflows

**Knowledge Graph Build**:

```
PDF → DoclingDocument → HybridChunker → Chunks
    → GLiNER + Groq NER → Entities + Relationships
    → Neo4j (Entity/Chunk/Section nodes + edges)
    → BGE-M3 Embeddings → Vector Index
```

**Summarization**:

```
Neo4j Graph + Figures → Vector Search + Graph Queries + Figure Evidence
    → Cross-Encoder Reranking → LLM Field Answers → Synthesis
```

**QA**:

```
Query → Entity Extraction → Graph Neighborhood → HyDE Vector
    → Vector Search → Reranking → Context Assembly
    → LLM Answer → Faithfulness Verification
```

### Critical Implementation Details

1. **Rate limiting**: Token-aware TPM + interval RPM for Groq
2. **Canonical names**: Normalized deduplication preserves digit distinctions (GPT-3 ≠ GPT-4)
3. **Blacklists**: Universal (generic terms) + Runtime (paper-specific noise)
4. **Section exclusions**: Discussion/Conclusion blocked from evaluation/comparisons fields
5. **Figure safety net**: RESULT_CHART blocked from approach/architecture fields
6. **HyDE fallback**: If rerank score < 0.1, use raw query instead
7. **Checkpointing**: Per-chunk saves enable resume on interruption

### Quick Reference

```bash
# Build knowledge graph
uv run kg2.py data/paper.pdf

# Generate summary
uv run summarize.py

# Ask question
uv run qa_engine.py "What is the architecture?"

# Evaluate summaries
uv run eval_summary.py --gt ground_truth_joint.json
```

**Key Files**:

- `kg2.py` — Knowledge graph pipeline (Neo4j + Docling + GLiNER + Groq)
- `summarize.py` — GraphRAG summarization (fields + synthesis)
- `qa_engine.py` — QA with HyDE + cross-encoder + verification
- `eval_summary.py` — 4-axis evaluation (hit rate, faithfulness, density, structure)
- `ground_truth_joint.json` — Ground truth facts for evaluation
- `eval_results.json` — Evaluation results with leaderboard

---

_Generated from project analysis on 2026-05-15_
