# Islamic Source Finder (ISF)

## Overview

The Islamic Source Finder (ISF) is a multi-modal RAG system designed for the semantic retrieval of Quranic verses and Hadith references. It allows users to verify religious citations using text, images, audio, or video inputs.

## Problem Statement

Religious scriptures are often cited incorrectly or without context in digital media. Manually verifying these sources across voluminous physical or PDF collections is time-consuming and error-prone.

## Architecture

- **Input Processing**:
  - **Text**: Direct embedding.
  - **Image**: Groq Llama 4 Scout OCR extracts text.
  - **Audio**: Groq Whisper-Large-v3 transcribes speech.
  - **Video**: `yt-dlp` and `moviepy` extract audio for Whisper transcription.
- **Retrieval**: Uses a ChromaDB vector store with `all-MiniLM-L6-v2` embeddings to find relevant passages.
- **Interface**: Built with Streamlit for a clean, interactive experience.

## Key Technical Decisions

- **Multi-modal Pipeline**: Designed to handle raw YouTube URLs and social media screenshots to make source verification as low-friction as possible.
- **Singleton Architecture**: The `IslamicSourceFinderClient` is implemented as a singleton to maintain persistent DB connections and prevent model re-initialization.
- **Lazy Loading**: Embedding models are only loaded into memory when the first query is received.

## Implementation Details

- **Idempotent Ingestion**: Uses MD5 hashing of content to ensure that duplicate PDFs aren't ingested into the vector database.
- **Structural Metadata**: Uses regex-based boundary detection to preserve the "Book/Hadees" hierarchy during chunking, providing accurate citations in search results.

## Challenges & Solutions

- **Media Cleanup**: Integrated `atexit` hooks to ensure that temporary media artifacts (downloaded MP4s/WAVs) are purged even if the app crashes.
- **Memory Conservation**: Media files are streamed to disk rather than held in RAM, allowing for the processing of large video queries on low-resource environments.

## Tech Stack

- **Vector Engine**: ChromaDB
- **Embedding Model**: `all-MiniLM-L6-v2`
- **Vision AI**: Groq Llama 4 Scout
- **Audio AI**: Groq Whisper-Large-v3
- **Orchestration**: Python, Streamlit

## Results & Outcomes

Significantly reduces the time required for source verification from several minutes of manual searching to sub-second semantic retrieval.

## FAQ

**Q: How accurate is the OCR for Arabic text?**
A: We use high-performance vision models that are specifically prompted to recognize and preserve Arabic script and its diacritics.

**Q: Can I just paste a YouTube link?**
A: Yes. The system will automatically download the audio, transcribe it using Whisper, and then use the transcription to search the database.

**Q: Why not just use keyword search?**
A: Keyword search fails when the user provides a paraphrase or a translation that doesn't exactly match the database text. Semantic search finds the _meaning_ of the query, making it much more robust.
