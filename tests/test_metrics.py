from __future__ import annotations

import unittest

from rag_quality_lab.io import DatasetError
from rag_quality_lab.metrics import (
    answer_metrics,
    classification_metrics,
    contract_metrics,
    retrieval_metrics,
)


class ClassificationMetricsTests(unittest.TestCase):
    def test_reports_accuracy_macro_f1_groups_and_latency(self) -> None:
        gold = [
            {"id": "1", "group": "faq", "expected": {"intent": "question"}},
            {"id": "2", "group": "order", "expected": {"intent": "order"}},
            {"id": "3", "group": "order", "expected": {"intent": "order"}},
        ]
        predictions = [
            {"id": "1", "intent": "question", "latency_ms": 2.0},
            {"id": "2", "intent": "question", "latency_ms": 4.0},
            {"id": "3", "intent": "order", "latency_ms": 6.0},
        ]

        metrics = classification_metrics(gold, predictions)

        self.assertEqual(metrics["total"], 3)
        self.assertAlmostEqual(metrics["accuracy"], 2 / 3)
        self.assertAlmostEqual(metrics["macro_f1"], (2 / 3 + 2 / 3) / 2)
        self.assertEqual(metrics["by_group"]["faq"]["accuracy"], 1.0)
        self.assertEqual(metrics["latency_ms"]["p50"], 4.0)


class RetrievalMetricsTests(unittest.TestCase):
    def test_reports_recall_mrr_ndcg_and_missing_results(self) -> None:
        gold = [
            {"id": "q1", "relevant_doc_ids": ["a"]},
            {"id": "q2", "relevant_doc_ids": ["b", "c"]},
        ]
        run = [
            {"id": "q1", "retrieved_doc_ids": ["x", "a"], "latency_ms": 1.0},
        ]

        metrics = retrieval_metrics(gold, run)

        self.assertEqual(metrics["total"], 2)
        self.assertEqual(metrics["missing_results"], 1)
        self.assertAlmostEqual(metrics["mrr"], 0.25)
        self.assertAlmostEqual(metrics["recall_at_k"]["3"], 0.5)
        self.assertGreater(metrics["ndcg_at_k"]["3"], 0.0)

    def test_deduplicates_ranked_documents_and_keeps_ndcg_bounded(self) -> None:
        metrics = retrieval_metrics(
            [{"id": "q1", "relevant_doc_ids": ["a"]}],
            [{"id": "q1", "retrieved_doc_ids": ["a", "a", "a"]}],
        )

        self.assertEqual(metrics["duplicate_document_ids_removed"], 2)
        self.assertEqual(metrics["ndcg_at_k"]["3"], 1.0)
        self.assertLessEqual(metrics["ndcg_at_k"]["5"], 1.0)

    def test_rejects_invalid_k_values_and_latency(self) -> None:
        gold = [{"id": "q1", "relevant_doc_ids": ["a"]}]
        with self.assertRaises(DatasetError):
            retrieval_metrics(gold, [], k_values=(0, 3))
        with self.assertRaises(DatasetError):
            retrieval_metrics(
                gold,
                [{"id": "q1", "retrieved_doc_ids": ["a"], "latency_ms": float("nan")}],
            )
        with self.assertRaises(DatasetError):
            retrieval_metrics(
                gold,
                [{"id": "q1", "retrieved_doc_ids": ["a"], "latency_ms": -1}],
            )


class AnswerMetricsTests(unittest.TestCase):
    def test_reports_citation_and_required_fact_coverage(self) -> None:
        gold = [
            {
                "id": "a1",
                "relevant_doc_ids": ["returns"],
                "required_facts": ["fourteen days", "complete package"],
            }
        ]
        answers = [
            {
                "id": "a1",
                "answer": "Return it within fourteen days and keep the complete package.",
                "cited_doc_ids": ["returns", "unrelated"],
                "latency_ms": 5.0,
            }
        ]

        metrics = answer_metrics(gold, answers)

        self.assertEqual(metrics["citation_precision"], 0.5)
        self.assertEqual(metrics["citation_recall"], 1.0)
        self.assertEqual(metrics["required_fact_coverage"], 1.0)

    def test_required_fact_matching_preserves_phrase_order(self) -> None:
        gold = [
            {
                "id": "a1",
                "relevant_doc_ids": ["damage"],
                "required_facts": ["do not install"],
            }
        ]
        answers = [
            {
                "id": "a1",
                "answer": "You can install it; do not photograph it.",
                "cited_doc_ids": ["damage"],
            }
        ]

        metrics = answer_metrics(gold, answers)

        self.assertEqual(metrics["required_fact_coverage"], 0.0)


class ContractMetricsTests(unittest.TestCase):
    def test_checks_complete_decision_contract(self) -> None:
        gold = [
            {
                "id": "c1",
                "group": "prompt_injection",
                "expected": {
                    "intent": "fallback",
                    "action": "fallback_rag",
                    "min_confidence": 0.0,
                    "max_confidence": 0.45,
                    "questions": ["safety"],
                    "forbidden_actions": ["start_order"],
                    "requires_confirmation": True,
                },
            }
        ]
        prediction = [
            {
                "id": "c1",
                "intent": "fallback",
                "action": "fallback_rag",
                "confidence": 0.4,
                "questions": ["safety"],
                "requires_confirmation": True,
            }
        ]

        metrics = contract_metrics(gold, prediction)

        self.assertEqual(metrics["pass_rate"], 1.0)
        self.assertEqual(metrics["checks"]["forbidden_actions"]["violations"], 0)

    def test_missing_required_outputs_fail_contract(self) -> None:
        gold = [
            {
                "id": "c1",
                "expected": {
                    "intent": "order",
                    "action": "start_order",
                    "min_confidence": 0.8,
                    "max_confidence": 1.0,
                    "questions": ["delivery"],
                    "forbidden_actions": [],
                    "requires_confirmation": True,
                },
            }
        ]
        prediction = [
            {
                "id": "c1",
                "intent": "order",
                "action": "start_order",
                "confidence": 0.9,
            }
        ]

        metrics = contract_metrics(gold, prediction)

        self.assertEqual(metrics["pass_rate"], 0.0)
        self.assertEqual(metrics["checks"]["questions"]["missing_required_outputs"], 1)
        self.assertEqual(metrics["checks"]["confirmation"]["missing_required_outputs"], 1)


if __name__ == "__main__":
    unittest.main()
