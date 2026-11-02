# Ibo RAG

Source-cited question answering over PDF documents, with optional online search
when the user explicitly asks for it.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest tests/unit
```

