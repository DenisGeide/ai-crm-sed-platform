from __future__ import annotations

import re
from pathlib import Path
from time import perf_counter

from .io import load_jsonl

TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")


def tokens(text: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(text) if len(token) > 1}


def token_overlap_run(
    gold_path: str | Path,
    knowledge_path: str | Path,
    *,
    top_k: int = 5,
) -> list[dict[str, object]]:
    documents = load_jsonl(knowledge_path)
    indexed = [
        (str(document["id"]), tokens(f"{document.get('title', '')} {document.get('text', '')}"))
        for document in documents
    ]
    run: list[dict[str, object]] = []
    for query in load_jsonl(gold_path):
        started = perf_counter()
        query_tokens = tokens(str(query["query"]))
        ranked = sorted(
            indexed,
            key=lambda item: (-len(query_tokens.intersection(item[1])), item[0]),
        )
        run.append(
            {
                "id": query["id"],
                "retrieved_doc_ids": [document_id for document_id, _ in ranked[:top_k]],
                "latency_ms": (perf_counter() - started) * 1000,
            }
        )
    return run
