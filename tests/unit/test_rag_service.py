import pytest

from service.rag_service import answer


def test_answer_rejects_empty_question() -> None:
    with pytest.raises(ValueError):
        answer("  ")

