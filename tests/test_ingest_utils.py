from muse_rag.ingest import stable_chunk_id
from muse_rag.graph import _unique_sources
from langchain_core.documents import Document


def test_chunk_id_is_deterministic():
    assert stable_chunk_id("muse.pdf", 1, "hello") == stable_chunk_id("muse.pdf", 1, "hello")


def test_chunk_id_changes_with_content_or_page():
    first = stable_chunk_id("muse.pdf", 1, "hello")
    assert first != stable_chunk_id("muse.pdf", 1, "hello world")
    assert first != stable_chunk_id("muse.pdf", 2, "hello")


def test_unique_sources_deduplicates_same_page():
    docs = [
        Document(page_content="a", metadata={"source": "muse.pdf", "page": 2}),
        Document(page_content="b", metadata={"source": "muse.pdf", "page": 2}),
        Document(page_content="c", metadata={"source": "muse.pdf", "page": 3}),
    ]
    assert _unique_sources(docs) == [
        {"source": "muse.pdf", "page": 2},
        {"source": "muse.pdf", "page": 3},
    ]
