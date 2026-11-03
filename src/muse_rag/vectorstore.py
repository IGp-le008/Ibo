"""Persistent Chroma store factory."""
from langchain_chroma import Chroma

from muse_rag.config import settings
from muse_rag.embeddings import get_embeddings


def get_vector_store() -> Chroma:
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )
