"""Single service entry point shared by CLI and API."""


def answer(question: str) -> str:
    """Return a clear placeholder until retrieval and generation are implemented."""
    if not question.strip():
        raise ValueError("question must not be empty")
    return "RAG service is not configured yet."

