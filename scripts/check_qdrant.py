"""Inspect the named-vector corpus without changing it."""
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.config import EMBED_MODEL, VECTOR_NAME, VECTOR_SIZE, collection_name


def inspect_collection(client, collection, require_model=False, require_project_index=False):
    info = client.get_collection(collection)
    vectors = info.config.params.vectors
    if not isinstance(vectors, dict) or VECTOR_NAME not in vectors:
        raise ValueError(f"Collection must have named vector {VECTOR_NAME}")
    vector = vectors[VECTOR_NAME]
    if vector.size != VECTOR_SIZE or vector.distance != Distance.COSINE:
        raise ValueError(f"Expected {VECTOR_NAME}: {VECTOR_SIZE} dimensions with cosine distance")
    count = client.count(collection_name=collection, exact=True).count
    if count <= 0:
        raise ValueError("Collection is empty")
    records, _ = client.scroll(collection_name=collection, limit=1, with_payload=True, with_vectors=False)
    model = (records[0].payload or {}).get("embedding_model") if records else None
    if model is not None and model != EMBED_MODEL:
        raise ValueError("Stored embedding model does not match the query model")
    if require_model and model != EMBED_MODEL:
        raise ValueError("Collection has no embedding model metadata")
    index = (getattr(info, 'payload_schema', None) or {}).get('project')
    project_index = getattr(index, 'data_type', None)
    if require_project_index and project_index != 'keyword':
        raise ValueError("Collection needs a keyword project index for scoped retrieval")
    aliases = [a.collection_name for a in client.get_aliases().aliases if a.alias_name == collection]
    return {"collection": collection, "target": aliases[0] if aliases else collection,
            "points": count, "vector": VECTOR_NAME, "dimensions": vector.size,
            "distance": str(vector.distance), "model": model or "unknown (legacy corpus)",
            "project_index": str(project_index) if project_index else None}


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env.local')
    if not os.getenv('QDRANT_URL'):
        raise ValueError("Configure QDRANT_URL before inspecting the corpus")
    client = QdrantClient(url=os.environ['QDRANT_URL'], api_key=os.getenv('QDRANT_API_KEY'), timeout=8)
    for key, value in inspect_collection(client, collection_name()).items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()
