"""OpenAI-compatible embeddings client configured for OpenRouter."""
from langchain_openai import OpenAIEmbeddings

from muse_rag.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    settings.validate_for_embeddings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        base_url=settings.base_url,
        api_key=settings.effective_embedding_key,
        # Some OpenAI-compatible providers do not expose token-count endpoints.
        check_embedding_ctx_length=False,
        model_kwargs={"encoding_format": "float"},
    )
