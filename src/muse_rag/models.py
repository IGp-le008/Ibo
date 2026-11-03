"""Typed state and output models used by the LangGraph workflow."""
from __future__ import annotations

from typing import TypedDict
from langchain_core.documents import Document


class RAGState(TypedDict, total=False):
    question: str
    search_query: str
    documents: list[Document]
    relevant: bool
    rewrite_count: int
    answer: str
    sources: list[dict[str, str | int]]


class GradeResult(TypedDict):
    relevant: bool
    reason: str
