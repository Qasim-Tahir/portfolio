"""Build and verify a replacement corpus before atomically switching its alias."""
import argparse
import hashlib
import os
import sys
from pathlib import Path
import re
import uuid

from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct, Document, VectorParams, Distance, CreateAliasOperation,
    CreateAlias, DeleteAliasOperation, DeleteAlias,
)
try:
    from scripts.check_qdrant import EMBED_MODEL, VECTOR_NAME, VECTOR_SIZE, inspect_collection
except ModuleNotFoundError:
    from check_qdrant import EMBED_MODEL, VECTOR_NAME, VECTOR_SIZE, inspect_collection

ROOT = Path(__file__).resolve().parents[1]
# Scripts can also be run directly from their directory.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.evidence import SOURCE_PROJECTS
from server.config import collection_name
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


def corpus_points(docs_dir):
    files = sorted(Path(docs_dir).glob('*.md'))
    if not files:
        raise ValueError("No Markdown documents found")
    headers = MarkdownHeaderTextSplitter(headers_to_split_on=[('##', 'section'), ('###', 'subsection')])
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    points = []
    for file in files:
        content = file.read_text(encoding='utf-8')
        if not content.strip():
            raise ValueError(f"Empty document: {file.name}")
        if re.search(r'(?:gsk_|sk-)[a-zA-Z0-9_-]{16,}', content):
            raise ValueError(f"Possible credential in document: {file.name}")
        for name in ('GROQ_API_KEY', 'QDRANT_API_KEY', 'QDRANT_URL', 'UPSTASH_REDIS_REST_TOKEN', 'UPSTASH_REDIS_REST_URL'):
            secret = os.getenv(name, '')
            if len(secret) >= 8 and secret in content:
                raise ValueError(f"Private configuration in document: {file.name}")
        document_hash = hashlib.sha256(content.encode()).hexdigest()
        start = len(points)
        for section in headers.split_text(content):
            for index, chunk in enumerate(splitter.split_text(section.page_content)):
                if len(chunk.strip()) < 50:
                    continue
                payload = {"text": chunk, "source": file.stem,
                           "project": SOURCE_PROJECTS.get(file.stem.removesuffix("-technical"), file.stem),
                           "section": section.metadata.get('section', ''),
                           "subsection": section.metadata.get('subsection', ''),
                           "document_hash": document_hash, "embedding_model": EMBED_MODEL}
                identity = f"{file.name}:{payload['section']}:{payload['subsection']}:{index}:{chunk}"
                points.append(PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, identity)),
                    vector={VECTOR_NAME: Document(text=chunk, model=EMBED_MODEL)}, payload=payload))
        if len(points) == start:
            raise ValueError(f"Document produced no usable chunks: {file.name}")
    if len({point.id for point in points}) != len(points):
        raise ValueError("Duplicate chunk IDs in corpus")
    return points


def alias_target(client, alias):
    return next((a.collection_name for a in client.get_aliases().aliases if a.alias_name == alias), None)


def switch_alias(client, alias, target):
    previous = alias_target(client, alias)
    if previous is None and client.collection_exists(alias):
        raise ValueError(f"{alias} is a physical collection. Use a new alias such as {alias}-live, then configure COLLECTION_NAME to that alias.")
    operations = []
    if previous is not None:
        operations.append(DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=alias)))
    operations.append(CreateAliasOperation(create_alias=CreateAlias(alias_name=alias, collection_name=target)))
    if not client.update_collection_aliases(change_aliases_operations=operations):
        raise RuntimeError("Alias switch was not acknowledged")
    return previous


def refresh(client, alias, points):
    if not points:
        raise ValueError("Cannot publish an empty corpus")
    if alias_target(client, alias) is None and client.collection_exists(alias):
        raise ValueError(f"{alias} is a physical collection. Choose a new --alias; the existing collection is retained.")
    version = f"{alias}-{uuid.uuid4().hex[:12]}"
    client.create_collection(collection_name=version,
        vectors_config={VECTOR_NAME: VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)})
    # Never delete the served collection, including when embedding/upload fails.
    for start in range(0, len(points), 50):
        client.upsert(collection_name=version, points=points[start:start + 50], wait=True)
    report = inspect_collection(client, version, require_model=True)
    if report['points'] != len(points):
        raise ValueError("Replacement point count does not match the corpus")
    result = client.query_points(collection_name=version, using=VECTOR_NAME,
        query=Document(text=points[0].payload['text'], model=EMBED_MODEL), limit=1, with_payload=True)
    if not result.points or not (result.points[0].payload or {}).get('text'):
        raise ValueError("Replacement retrieval smoke check failed")
    previous = switch_alias(client, alias, version)
    return version, previous


def rollback(client, alias, target):
    if alias == target:
        raise ValueError("Rollback target must be a physical version collection")
    inspect_collection(client, target)
    return switch_alias(client, alias, target)


def main():
    load_dotenv(ROOT / '.env.local')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alias', default=collection_name())
    parser.add_argument('--docs', type=Path, default=ROOT / 'docs')
    parser.add_argument('--rollback-to', help='Retained physical collection to reactivate')
    args = parser.parse_args()
    # Read and validate every file before creating a remote collection.
    points = None if args.rollback_to else corpus_points(args.docs)
    if not os.getenv('QDRANT_URL'):
        raise ValueError("Configure QDRANT_URL before ingesting")
    client = QdrantClient(url=os.environ['QDRANT_URL'], api_key=os.getenv('QDRANT_API_KEY'), cloud_inference=True, timeout=30)
    if args.rollback_to:
        previous = rollback(client, args.alias, args.rollback_to)
        version = args.rollback_to
    else:
        version, previous = refresh(client, args.alias, points)
    print(f"Alias {args.alias} now serves {version}. Configure COLLECTION_NAME={args.alias} in both API and ingestion environments.")
    print(f"Previous collection retained: {previous or 'none (first alias activation)'}")
    if previous:
        print(f"Rollback: python scripts/ingest.py --alias {args.alias} --rollback-to {previous}")


if __name__ == '__main__':
    main()
