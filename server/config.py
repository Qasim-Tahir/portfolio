"""Shared collection and embedding configuration for API and corpus tools."""
import os

DEFAULT_COLLECTION = 'portfolio-live'
EMBED_MODEL = 'sentence-transformers/all-minilm-l6-v2'
VECTOR_NAME = 'content_vector'
VECTOR_SIZE = 384


def collection_name():
    return os.getenv('COLLECTION_NAME', DEFAULT_COLLECTION)
