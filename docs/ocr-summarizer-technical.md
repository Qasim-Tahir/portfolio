# LuminaNotes: implementation notes

## Scope
This is a scoped description from the public portfolio and supplied narrative. External performance measurements have not been supplied.

## Architecture
Book_processor.py configures meta-llama/llama-4-scout-17b-16e-instruct for vision extraction and summarization.

The project converts slides to PDF with LibreOffice, extracts page images with Poppler, and transcribes video audio with Whisper.

Entity checks compare names and other extracted entities with OCR text. Entity presence does not validate relationships, quantities, omissions, or factual accuracy.

## Verified model configuration
Book_processor.py at public revision d6098da871beec35870ae14efeffaf6ddfdb6ed8 configures meta-llama/llama-4-scout-17b-16e-instruct. The portfolio previously said Llama 3 Vision; the current summary uses Llama 4 Scout. This verifies the configured identifier, not current provider availability.

## Validation limits
Entity checks can flag unsupported entities, but an entity may appear in the source while a generated relationship or quantity is wrong. Layout fidelity and note-taking-time reductions have no reproducible dataset or raw results here.
