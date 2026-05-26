import os, glob, uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Document, VectorParams, Distance
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Load from the root .env.local relative to this script
env_path = os.path.join(os.path.dirname(__file__), "..", ".env.local")
load_dotenv(env_path)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("COLLECTION_NAME", "portfolio")
EMBED_MODEL = "sentence-transformers/all-minilm-l6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

if not QDRANT_URL or not QDRANT_API_KEY:
    print("Error: QDRANT_URL or QDRANT_API_KEY is not configured in .env.local")
    exit(1)

# Initialize Qdrant with Cloud Inference enabled
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, cloud_inference=True)

# Delete and recreate collection cleanly with named vector tied to the model
if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)
    print(f"Deleted existing collection: {COLLECTION}")

VECTOR_NAME = "content_vector"

client.create_collection(
    collection_name=COLLECTION,
    vectors_config={
        VECTOR_NAME: VectorParams(size=384, distance=Distance.COSINE)
    }
)
print(f"Created collection: {COLLECTION} with named vector: {EMBED_MODEL}")

# Header-aware splitting preserves document structure
header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "section"), ("###", "subsection")]
)
char_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)

points = []
# Find all markdown files in the docs/ directory
docs_path = os.path.join(os.path.dirname(__file__), "..", "docs", "*.md")
for filepath in glob.glob(docs_path):
    doc_name = os.path.basename(filepath).replace(".md", "")
    print(f"Processing: {doc_name}")
    with open(filepath, "r") as f:
        content = f.read()

    header_chunks = header_splitter.split_text(content)
    for hchunk in header_chunks:
        sub_chunks = char_splitter.split_text(hchunk.page_content)
        for chunk in sub_chunks:
            if len(chunk.strip()) < 50:   # skip tiny fragments
                continue
            
            # Using Qdrant Cloud Inference: Just pass the text and model name
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    VECTOR_NAME: Document(
                        text=chunk,
                        model=EMBED_MODEL
                    )
                },
                payload={
                    "text": chunk,
                    "source": doc_name,
                    "section": hchunk.metadata.get("section", ""),
                    "subsection": hchunk.metadata.get("subsection", "")
                }
            ))

# Upsert in batches
batch_size = 50 # smaller batch for cloud inference
for i in range(0, len(points), batch_size):
    client.upsert(collection_name=COLLECTION, points=points[i:i+batch_size])
    print(f"Upserted {min(i+batch_size, len(points))}/{len(points)} chunks")

print(f"\n✅ Done. Total chunks ingested: {len(points)} using Qdrant Cloud Inference")
