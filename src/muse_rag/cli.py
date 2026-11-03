"""Interactive CLI for the Agentic RAG app."""
from __future__ import annotations

import logging
import sys

from muse_rag.graph import ask


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    print("Muse PDF Agentic RAG — type 'exit' or 'quit' to stop.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not question:
            continue
        try:
            result = ask(question)
            print(f"\nAssistant: {result['answer']}")
            if result["sources"]:
                print("\nSources:")
                for source in result["sources"]:
                    print(f"  - {source['source']}, page {source['page']}")
            if result["rewrite_count"]:
                print(f"\n[Search query rewrites: {result['rewrite_count']}]")
        except Exception as exc:
            print(f"\nError: {exc}", file=sys.stderr)
            print(
                "Check .env, the configured model IDs, API credits/rate limits, "
                "and whether the PDF has been indexed.",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
