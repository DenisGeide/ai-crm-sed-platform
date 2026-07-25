from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from rag_quality_lab.cli import main
from rag_quality_lab.io import load_jsonl
from rag_quality_lab.metrics import (
    answer_metrics,
    classification_metrics,
    contract_metrics,
    retrieval_metrics,
)

ROOT = Path(__file__).resolve().parents[1]


class PublicFixtureTests(unittest.TestCase):
    def test_public_datasets_have_stable_counts_and_unique_ids(self) -> None:
        intent = load_jsonl(ROOT / "evaluation" / "datasets" / "intent_v1.jsonl")
        retrieval = load_jsonl(ROOT / "evaluation" / "datasets" / "rag_gold_v1.jsonl")
        answers = load_jsonl(ROOT / "evaluation" / "datasets" / "answer_gold_v1.jsonl")
        knowledge = load_jsonl(ROOT / "evaluation" / "fixtures" / "knowledge_base.jsonl")

        self.assertEqual(len(intent), 118)
        self.assertEqual(len(retrieval), 30)
        self.assertEqual(len(answers), 12)
        self.assertEqual(len(knowledge), 12)
        for rows in (intent, retrieval, answers, knowledge):
            ids = [row["id"] for row in rows]
            self.assertEqual(len(ids), len(set(ids)))

    def test_intent_fixture_contains_no_email_or_original_demo_phone(self) -> None:
        raw = (ROOT / "evaluation" / "datasets" / "intent_v1.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("client@example.com", raw)
        self.assertNotIn("+7 999 123-45-67", raw)

    def test_demo_generates_machine_and_human_readable_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            output = Path(temp_directory) / "demo"
            with redirect_stdout(StringIO()):
                code = main(["demo", "--output", str(output)])
            self.assertEqual(code, 0)
            self.assertTrue(output.with_suffix(".json").is_file())
            self.assertTrue(output.with_suffix(".md").is_file())
            run_path = output.with_name("demo-run.jsonl")
            self.assertTrue(run_path.is_file())
            self.assertEqual(len(load_jsonl(run_path)), 30)

            with redirect_stdout(StringIO()):
                round_trip_code = main(
                    [
                        "retrieval",
                        "--gold",
                        str(ROOT / "evaluation" / "datasets" / "rag_gold_v1.jsonl"),
                        "--run",
                        str(run_path),
                        "--output",
                        str(Path(temp_directory) / "round-trip"),
                    ]
                )
            self.assertEqual(round_trip_code, 0)

    def test_committed_metrics_match_public_fixtures(self) -> None:
        intent_gold = load_jsonl(ROOT / "evaluation" / "datasets" / "intent_v1.jsonl")
        intent_run = load_jsonl(ROOT / "evaluation" / "runs" / "deterministic_pipeline_v1.jsonl")
        answer_gold = load_jsonl(ROOT / "evaluation" / "datasets" / "answer_gold_v1.jsonl")
        answer_run = load_jsonl(ROOT / "evaluation" / "runs" / "answer_contract_fixture_v1.jsonl")
        retrieval_gold = load_jsonl(ROOT / "evaluation" / "datasets" / "rag_gold_v1.jsonl")
        retrieval_run = load_jsonl(ROOT / "reports" / "synthetic-retrieval-v1-run.jsonl")

        expected_reports = {
            "intent-regression-v1.json": classification_metrics(intent_gold, intent_run),
            "action-regression-v1.json": classification_metrics(
                intent_gold,
                intent_run,
                expected_field="action",
                predicted_field="action",
            ),
            "contract-regression-v1.json": contract_metrics(intent_gold, intent_run),
            "answer-contract-v1.json": answer_metrics(answer_gold, answer_run),
            "synthetic-retrieval-v1.json": retrieval_metrics(
                retrieval_gold,
                retrieval_run,
            ),
        }
        for filename, expected in expected_reports.items():
            actual = json.loads((ROOT / "reports" / filename).read_text(encoding="utf-8"))
            self.assertEqual(actual, expected, filename)


if __name__ == "__main__":
    unittest.main()
