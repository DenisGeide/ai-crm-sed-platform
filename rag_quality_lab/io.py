from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class DatasetError(ValueError):
    """Raised when an evaluation fixture is malformed."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    records: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetError(f"{source}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise DatasetError(f"{source}:{line_number}: each JSONL row must be an object")
            records.append(payload)
    if not records:
        raise DatasetError(f"{source}: dataset is empty")
    return records


def write_json(path: str | Path, payload: Any) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    destination.write_text(payload, encoding="utf-8")
    return destination


def rows_by_id(rows: Iterable[dict[str, Any]], *, source: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            raise DatasetError(f"{source}: every row requires a non-empty string id")
        if record_id in indexed:
            raise DatasetError(f"{source}: duplicate id {record_id!r}")
        indexed[record_id] = row
    return indexed
