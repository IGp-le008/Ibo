"""Environment-backed application settings."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _project_path(value: str, default: str) -> Path:
    path = Path(os.getenv(value, default)).expanduser()
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    chat_api_key: str = os.getenv("CHAT_API_KEY", "")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    base_url: str = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
    chat_model: str = os.getenv("CHAT_MODEL", "nvidia/nemotron-3.5-lightning:free")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nvidia/nemotron-3.5-embed-1b:free")
    pdf_path: Path = _project_path("PDF_PATH", "./data/muse.pdf")
    chroma_dir: Path = _project_path("CHROMA_DIR", "./storage/chroma")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "muse_pdf")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "5"))
    max_rewrites: int = int(os.getenv("MAX_REWRITES", "2"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.4"))

    @property
    def effective_embedding_key(self) -> str:
        return self.embedding_api_key or self.chat_api_key

    def validate_for_chat(self) -> None:
        if not self.chat_api_key:
            raise RuntimeError(
                "CHAT_API_KEY is missing. Copy .env.example to .env and set your key."
            )

    def validate_for_embeddings(self) -> None:
        if not self.embedding_api_key:
            raise RuntimeError(
                "Set EMBEDDING_API_KEY or CHAT_API_KEY in .env."
            )


settings = Settings()
