# scripts/check_qdrant.py
from dotenv import load_dotenv
import os
load_dotenv('.env.local')

from qdrant_client import QdrantClient

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
collection = os.getenv("COLLECTION_NAME", "portfolio")

info = client.get_collection(collection)
print(f"Collection: {collection}")
print(f"Points count: {info.points_count}")
print(f"Vector size: {info.config.params.vectors.size}")