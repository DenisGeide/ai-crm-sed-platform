from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from importlib.resources import as_file, files
from pathlib import Path
from typing import Sequence

from .demo import token_overlap_run
from .io import DatasetError, load_jsonl, write_json, write_jsonl
from .metrics import answer_metrics, classification_metrics, contract_metrics, retrieval_metrics
from .reporting import markdown_report

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _bundled_or_repository_resource(name: str, fallback: Path):
    bundled = files("rag_quality_lab").joinpath("resources", name)
    return bundled if bundled.is_file() else fallback


DEFAULT_RAG_GOLD = _bundled_or_repository_resource(
    "rag_gold_v1.jsonl",
    REPOSITORY_ROOT / "evaluation" / "datasets" / "rag_gold_v1.jsonl",
)
DEFAULT_KNOWLEDGE = _bundled_or_repository_resource(
    "knowledge_base.jsonl",
    REPOSITORY_ROOT / "evaluation" / "fixtures" / "knowledge_base.jsonl",
)


def _write_reports(metrics: dict, output: Path, title: str) -> None:
    write_json(output.with_suffix(".json"), metrics)
    output.with_suffix(".md").write_text(
        markdown_report(metrics, title=title),
        encoding="utf-8",
    )


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-quality-lab",
        description="Evaluate intent predictions and RAG retrieval runs with public JSONL contracts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    intent = subparsers.add_parser("intent", help="Evaluate intent predictions.")
    intent.add_argument("--gold", type=Path, required=True)
    intent.add_argument("--predictions", type=Path, required=True)
    intent.add_argument("--output", type=Path, default=Path("reports/intent-evaluation"))
    intent.add_argument("--expected-field", default="intent")
    intent.add_argument("--predicted-field", default="intent")

    contract = subparsers.add_parser("contract", help="Evaluate the full decision contract.")
    contract.add_argument("--gold", type=Path, required=True)
    contract.add_argument("--predictions", type=Path, required=True)
    contract.add_argument("--output", type=Path, default=Path("reports/contract-evaluation"))

    retrieval = subparsers.add_parser("retrieval", help="Evaluate a retrieval run.")
    retrieval.add_argument("--gold", type=Path, required=True)
    retrieval.add_argument("--run", type=Path, required=True)
    retrieval.add_argument("--output", type=Path, default=Path("reports/retrieval-evaluation"))

    answer = subparsers.add_parser("answer", help="Evaluate citations and required-fact coverage.")
    answer.add_argument("--gold", type=Path, required=True)
    answer.add_argument("--answers", type=Path, required=True)
    answer.add_argument("--output", type=Path, default=Path("reports/answer-evaluation"))

    demo = subparsers.add_parser("demo", help="Run the dependency-free token-overlap demo.")
    demo.add_argument("--gold", type=Path)
    demo.add_argument("--knowledge", type=Path)
    demo.add_argument("--output", type=Path, default=Path("reports/demo-retrieval"))
    demo.add_argument("--top-k", type=_positive_integer, default=5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "intent":
            metrics = classification_metrics(
                load_jsonl(args.gold),
                load_jsonl(args.predictions),
                expected_field=args.expected_field,
                predicted_field=args.predicted_field,
            )
            title = f"{args.expected_field.replace('_', ' ').title()} Evaluation"
        elif args.command == "contract":
            metrics = contract_metrics(
                load_jsonl(args.gold),
                load_jsonl(args.predictions),
            )
            title = "Decision Contract Evaluation"
        elif args.command == "retrieval":
            metrics = retrieval_metrics(load_jsonl(args.gold), load_jsonl(args.run))
            title = "Retrieval Evaluation"
        elif args.command == "answer":
            metrics = answer_metrics(load_jsonl(args.gold), load_jsonl(args.answers))
            title = "Answer Contract Evaluation"
        else:
            with ExitStack() as stack:
                gold_path = args.gold or stack.enter_context(as_file(DEFAULT_RAG_GOLD))
                knowledge_path = args.knowledge or stack.enter_context(as_file(DEFAULT_KNOWLEDGE))
                run = token_overlap_run(
                    gold_path,
                    knowledge_path,
                    top_k=args.top_k,
                )
                metrics = retrieval_metrics(load_jsonl(gold_path), run)
            run_path = args.output.with_name(f"{args.output.name}-run.jsonl")
            write_jsonl(run_path, run)
            title = "Synthetic Retrieval Demo"
        _write_reports(metrics, args.output, title)
    except (DatasetError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0
