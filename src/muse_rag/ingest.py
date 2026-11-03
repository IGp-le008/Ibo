"""PDF ingestion command: load -> split -> embed -> persist in Chroma."""
from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from muse_rag.config import settings
from muse_rag.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


def stable_chunk_id(source: str, page_number: int, content: str) -> str:
    """Return a deterministic ID for a source page and chunk."""
    payload = f"{source}|{page_number}|{content}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_and_split_pdf(pdf_path: Path) -> list[Document]:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}\nPlace muse.pdf at ./data/muse.pdf "
            "or set PDF_PATH in .env."
        )
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {pdf_path}")

    pages = PyPDFLoader(str(pdf_path)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    source_name = pdf_path.name

    for chunk in chunks:
        # PyPDFLoader page indices are zero-based. Keep both for traceability.
        zero_based_page = int(chunk.metadata.get("page", 0))
        chunk.metadata.update(
            {
                "source": source_name,
                "page": zero_based_page + 1,
                "page_index": zero_based_page,
                "file_path": str(pdf_path.resolve()),
            }
        )
    return chunks


def ingest_pdf(pdf_path: Path | None = None) -> int:
    path = (pdf_path or settings.pdf_path).resolve()
    chunks = load_and_split_pdf(path)
    if not chunks:
        raise ValueError(f"No text chunks extracted from {path}. Is this a scanned PDF?")

    store = get_vector_store()
    source_name = path.name

    # Replace this source's previous chunks so changed PDFs do not leave stale
    # chunks behind. Other sources in the same collection are preserved.
    existing = store.get(where={"source": source_name})
    old_ids = existing.get("ids", [])
    if old_ids:
        store.delete(ids=old_ids)
        logger.info("Removed %d previous chunks for %s", len(old_ids), source_name)

    ids = [
        stable_chunk_id(source_name, int(doc.metadata["page"]), doc.page_content)
        for doc in chunks
    ]
    store.add_documents(documents=chunks, ids=ids)
    logger.info("Indexed %d chunks from %s into Chroma.", len(chunks), path)
    return len(chunks)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Index a PDF into the local Chroma database.")
    parser.add_argument("--pdf", type=Path, default=None, help="Optional PDF path.")
    args = parser.parse_args()
    count = ingest_pdf(args.pdf)
    print(f"Indexed {count} chunks into collection '{settings.collection_name}'.")


if __name__ == "__main__":
    main()
