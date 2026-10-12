# Islamic Source Finder: implementation notes

## Scope
This is a scoped description from the public portfolio and supplied narrative. External performance measurements have not been supplied.

## Architecture
The project describes text embeddings with sentence-transformers/all-MiniLM-L6-v2 and a ChromaDB vector store.

OCR and Whisper transcription turn image and audio/video queries into searchable text.

Retrieved passages help a visitor locate sources. Similarity does not establish authenticity, doctrinal correctness, or an authoritative religious judgment. No latency benchmark is published here.
