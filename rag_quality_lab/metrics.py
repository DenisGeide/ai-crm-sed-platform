from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Iterable
from statistics import mean
from typing import Any

from .io import DatasetError, rows_by_id

TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _f1(true_positive: int, false_positive: int, false_negative: int) -> float:
    denominator = (2 * true_positive) + false_positive + false_negative
    return (2 * true_positive / denominator) if denominator else 0.0


def _expected_payload(gold_row: dict[str, Any], *, record_id: str) -> dict[str, Any]:
    expected = gold_row.get("expected")
    if not isinstance(expected, dict):
        raise DatasetError(f"gold id {record_id!r} requires an expected object")
    return expected


def _latency_value(row: dict[str, Any], *, record_id: str, source: str) -> float | None:
    raw_latency = row.get("latency_ms")
    if raw_latency is None:
        return None
    if isinstance(raw_latency, bool):
        raise DatasetError(f"{source} id {record_id!r} has invalid latency_ms")
    try:
        latency = float(raw_latency)
    except (TypeError, ValueError) as exc:
        raise DatasetError(f"{source} id {record_id!r} has invalid latency_ms") from exc
    if not math.isfinite(latency) or latency < 0:
        raise DatasetError(f"{source} id {record_id!r} requires finite non-negative latency_ms")
    return latency


def _string_list(value: Any, *, record_id: str, field: str, source: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise DatasetError(f"{source} id {record_id!r} requires {field} as a list of strings")
    return value


def classification_metrics(
    gold_rows: Iterable[dict[str, Any]],
    prediction_rows: Iterable[dict[str, Any]],
    *,
    expected_field: str = "intent",
    predicted_field: str = "intent",
) -> dict[str, Any]:
    gold = rows_by_id(gold_rows, source="gold")
    predictions = rows_by_id(prediction_rows, source="predictions")
    unknown_ids = sorted(set(predictions) - set(gold))
    if unknown_ids:
        raise DatasetError(f"predictions contain unknown ids: {unknown_ids[:5]}")

    labels: set[str] = set()
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    groups: dict[str, list[bool]] = defaultdict(list)
    latencies: list[float] = []
    correct = 0
    missing = 0

    for record_id, gold_row in gold.items():
        expected = _expected_payload(gold_row, record_id=record_id).get(expected_field)
        if not isinstance(expected, str):
            raise DatasetError(f"gold id {record_id!r} lacks expected.{expected_field}")
        labels.add(expected)
        prediction = predictions.get(record_id)
        if prediction is None:
            predicted = "__missing__"
            missing += 1
        else:
            predicted = prediction.get(predicted_field, "__missing__")
            if not isinstance(predicted, str):
                raise DatasetError(f"prediction id {record_id!r} has invalid {predicted_field}")
            latency = _latency_value(prediction, record_id=record_id, source="prediction")
            if latency is not None:
                latencies.append(latency)
        labels.add(predicted)
        passed = expected == predicted
        correct += int(passed)
        confusion[expected][predicted] += 1
        groups[str(gold_row.get("group", "ungrouped"))].append(passed)

    per_class: dict[str, dict[str, float | int]] = {}
    f1_scores: list[float] = []
    for label in sorted(labels):
        if label == "__missing__":
            continue
        tp = confusion[label].get(label, 0)
        fp = sum(confusion[other].get(label, 0) for other in labels if other != label)
        fn = sum(count for predicted, count in confusion[label].items() if predicted != label)
        score = _f1(tp, fp, fn)
        f1_scores.append(score)
        per_class[label] = {"support": sum(confusion[label].values()), "f1": score}

    total = len(gold)
    return {
        "schema_version": "1.0",
        "task": "classification",
        "total": total,
        "correct": correct,
        "missing_predictions": missing,
        "accuracy": correct / total if total else 0.0,
        "macro_f1": mean(f1_scores) if f1_scores else 0.0,
        "latency_ms": {
            "samples": len(latencies),
            "mean": mean(latencies) if latencies else 0.0,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
        "by_group": {
            group: {"total": len(results), "accuracy": sum(results) / len(results)}
            for group, results in sorted(groups.items())
        },
        "per_class": per_class,
        "confusion": {
            expected: dict(sorted(predicted.items())) for expected, predicted in sorted(confusion.items())
        },
    }


def contract_metrics(
    gold_rows: Iterable[dict[str, Any]],
    prediction_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate the complete public decision contract.

    Missing question and confirmation outputs are failures whenever the gold
    contract requires those outputs. This keeps partial snapshots honest.
    """

    gold = rows_by_id(gold_rows, source="gold")
    predictions = rows_by_id(prediction_rows, source="predictions")
    unknown_ids = sorted(set(predictions) - set(gold))
    if unknown_ids:
        raise DatasetError(f"predictions contain unknown ids: {unknown_ids[:5]}")

    total = len(gold)
    missing_predictions = 0
    overall_passed = 0
    intent_passed = 0
    action_passed = 0
    confidence_passed = 0
    question_passed = 0
    missing_required_questions = 0
    confirmation_samples = 0
    confirmation_passed = 0
    missing_required_confirmations = 0
    forbidden_samples = 0
    forbidden_violations = 0
    latencies: list[float] = []
    groups: dict[str, list[bool]] = defaultdict(list)

    for record_id, gold_row in gold.items():
        expected = _expected_payload(gold_row, record_id=record_id)
        expected_intent = expected.get("intent")
        expected_action = expected.get("action")
        if not isinstance(expected_intent, str) or not isinstance(expected_action, str):
            raise DatasetError(f"gold id {record_id!r} requires expected intent and action")

        minimum = expected.get("min_confidence")
        maximum = expected.get("max_confidence")
        if (
            isinstance(minimum, bool)
            or isinstance(maximum, bool)
            or not isinstance(minimum, (int, float))
            or not isinstance(maximum, (int, float))
            or not math.isfinite(float(minimum))
            or not math.isfinite(float(maximum))
            or float(minimum) > float(maximum)
        ):
            raise DatasetError(f"gold id {record_id!r} has invalid confidence bounds")

        expected_questions = _string_list(
            expected.get("questions"),
            record_id=record_id,
            field="expected.questions",
            source="gold",
        )
        forbidden_actions = _string_list(
            expected.get("forbidden_actions"),
            record_id=record_id,
            field="expected.forbidden_actions",
            source="gold",
        )
        expected_confirmation = expected.get("requires_confirmation")
        if expected_confirmation is not None and not isinstance(expected_confirmation, bool):
            raise DatasetError(f"gold id {record_id!r} has invalid expected.requires_confirmation")

        prediction = predictions.get(record_id)
        if prediction is None:
            missing_predictions += 1
            predicted_intent = None
            predicted_action = None
            confidence = None
            predicted_questions: list[str] = []
            predicted_confirmation = None
        else:
            predicted_intent = prediction.get("intent")
            predicted_action = prediction.get("action")
            confidence_raw = prediction.get("confidence")
            if confidence_raw is None:
                confidence = None
            elif isinstance(confidence_raw, bool):
                raise DatasetError(f"prediction id {record_id!r} has invalid confidence")
            else:
                try:
                    confidence = float(confidence_raw)
                except (TypeError, ValueError) as exc:
                    raise DatasetError(f"prediction id {record_id!r} has invalid confidence") from exc
                if not math.isfinite(confidence):
                    raise DatasetError(f"prediction id {record_id!r} has non-finite confidence")

            questions_raw = prediction.get("questions", [])
            predicted_questions = _string_list(
                questions_raw,
                record_id=record_id,
                field="questions",
                source="prediction",
            )
            predicted_confirmation = prediction.get("requires_confirmation")
            if predicted_confirmation is not None and not isinstance(predicted_confirmation, bool):
                raise DatasetError(f"prediction id {record_id!r} has invalid requires_confirmation")
            latency = _latency_value(prediction, record_id=record_id, source="prediction")
            if latency is not None:
                latencies.append(latency)

        intent_ok = predicted_intent == expected_intent
        action_ok = predicted_action == expected_action
        confidence_ok = confidence is not None and float(minimum) <= confidence <= float(maximum)
        questions_ok = set(predicted_questions) == set(expected_questions)
        if expected_questions and "questions" not in (prediction or {}):
            missing_required_questions += 1

        confirmation_ok = True
        if expected_confirmation is not None:
            confirmation_samples += 1
            confirmation_ok = predicted_confirmation == expected_confirmation
            confirmation_passed += int(confirmation_ok)
            if "requires_confirmation" not in (prediction or {}):
                missing_required_confirmations += 1

        forbidden_ok = True
        if forbidden_actions:
            forbidden_samples += 1
            forbidden_ok = predicted_action not in forbidden_actions
            forbidden_violations += int(not forbidden_ok)

        passed = (
            intent_ok and action_ok and confidence_ok and questions_ok and confirmation_ok and forbidden_ok
        )
        intent_passed += int(intent_ok)
        action_passed += int(action_ok)
        confidence_passed += int(confidence_ok)
        question_passed += int(questions_ok)
        overall_passed += int(passed)
        groups[str(gold_row.get("group", "ungrouped"))].append(passed)

    def ratio(passed: int, samples: int) -> float:
        return passed / samples if samples else 0.0

    return {
        "schema_version": "1.0",
        "task": "contract",
        "total": total,
        "passed": overall_passed,
        "pass_rate": ratio(overall_passed, total),
        "missing_predictions": missing_predictions,
        "checks": {
            "intent": {"samples": total, "passed": intent_passed, "rate": ratio(intent_passed, total)},
            "action": {"samples": total, "passed": action_passed, "rate": ratio(action_passed, total)},
            "confidence_bounds": {
                "samples": total,
                "passed": confidence_passed,
                "rate": ratio(confidence_passed, total),
            },
            "questions": {
                "samples": total,
                "passed": question_passed,
                "rate": ratio(question_passed, total),
                "missing_required_outputs": missing_required_questions,
            },
            "confirmation": {
                "samples": confirmation_samples,
                "passed": confirmation_passed,
                "rate": ratio(confirmation_passed, confirmation_samples),
                "missing_required_outputs": missing_required_confirmations,
            },
            "forbidden_actions": {
                "samples": forbidden_samples,
                "passed": forbidden_samples - forbidden_violations,
                "rate": ratio(forbidden_samples - forbidden_violations, forbidden_samples),
                "violations": forbidden_violations,
            },
        },
        "latency_ms": {
            "samples": len(latencies),
            "mean": mean(latencies) if latencies else 0.0,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
        "by_group": {
            group: {"total": len(results), "pass_rate": sum(results) / len(results)}
            for group, results in sorted(groups.items())
        },
    }


def _dcg(retrieved: list[str], relevant: set[str], k: int) -> float:
    return sum(
        1.0 / math.log2(rank + 2) for rank, document_id in enumerate(retrieved[:k]) if document_id in relevant
    )


def retrieval_metrics(
    gold_rows: Iterable[dict[str, Any]],
    run_rows: Iterable[dict[str, Any]],
    *,
    k_values: tuple[int, ...] = (1, 3, 5),
) -> dict[str, Any]:
    if (
        not k_values
        or any(isinstance(k, bool) or not isinstance(k, int) or k <= 0 for k in k_values)
        or len(set(k_values)) != len(k_values)
    ):
        raise DatasetError("k_values must contain unique positive integers")

    gold = rows_by_id(gold_rows, source="gold")
    run = rows_by_id(run_rows, source="run")
    unknown_ids = sorted(set(run) - set(gold))
    if unknown_ids:
        raise DatasetError(f"run contains unknown ids: {unknown_ids[:5]}")

    recalls: dict[int, list[float]] = {k: [] for k in k_values}
    ndcgs: dict[int, list[float]] = {k: [] for k in k_values}
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    missing = 0
    duplicate_document_ids_removed = 0

    for query_id, gold_row in gold.items():
        relevant_raw = gold_row.get("relevant_doc_ids")
        if not isinstance(relevant_raw, list) or not relevant_raw:
            raise DatasetError(f"gold id {query_id!r} requires relevant_doc_ids")
        relevant = {str(value) for value in relevant_raw}
        result = run.get(query_id)
        if result is None:
            retrieved: list[str] = []
            missing += 1
        else:
            retrieved_raw = result.get("retrieved_doc_ids")
            if not isinstance(retrieved_raw, list):
                raise DatasetError(f"run id {query_id!r} requires retrieved_doc_ids")
            retrieved = []
            seen_document_ids: set[str] = set()
            for value in retrieved_raw:
                document_id = str(value)
                if document_id in seen_document_ids:
                    duplicate_document_ids_removed += 1
                    continue
                seen_document_ids.add(document_id)
                retrieved.append(document_id)
            latency = _latency_value(result, record_id=query_id, source="run")
            if latency is not None:
                latencies.append(latency)

        first_relevant_rank = next(
            (rank for rank, document_id in enumerate(retrieved, start=1) if document_id in relevant),
            None,
        )
        reciprocal_ranks.append(1.0 / first_relevant_rank if first_relevant_rank else 0.0)
        for k in k_values:
            hits = len(relevant.intersection(retrieved[:k]))
            recalls[k].append(hits / len(relevant))
            ideal_length = min(len(relevant), k)
            ideal_dcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_length))
            ndcgs[k].append(_dcg(retrieved, relevant, k) / ideal_dcg if ideal_dcg else 0.0)

    return {
        "schema_version": "1.0",
        "task": "retrieval",
        "total": len(gold),
        "missing_results": missing,
        "duplicate_document_ids_removed": duplicate_document_ids_removed,
        "mrr": mean(reciprocal_ranks),
        "recall_at_k": {str(k): mean(values) for k, values in recalls.items()},
        "ndcg_at_k": {str(k): mean(values) for k, values in ndcgs.items()},
        "latency_ms": {
            "samples": len(latencies),
            "mean": mean(latencies) if latencies else 0.0,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
    }


def _normalised_tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_RE.findall(text)]


def _contains_token_phrase(answer_tokens: list[str], fact_tokens: list[str]) -> bool:
    if not fact_tokens or len(fact_tokens) > len(answer_tokens):
        return False
    width = len(fact_tokens)
    return any(
        answer_tokens[index : index + width] == fact_tokens for index in range(len(answer_tokens) - width + 1)
    )


def answer_metrics(
    gold_rows: Iterable[dict[str, Any]],
    answer_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Score deterministic citation and required-fact coverage.

    This is intentionally a transparent proxy. It does not claim to measure
    semantic correctness or replace expert/LLM-assisted review.
    """

    gold = rows_by_id(gold_rows, source="gold")
    answers = rows_by_id(answer_rows, source="answers")
    unknown_ids = sorted(set(answers) - set(gold))
    if unknown_ids:
        raise DatasetError(f"answers contain unknown ids: {unknown_ids[:5]}")

    citation_precisions: list[float] = []
    citation_recalls: list[float] = []
    fact_coverages: list[float] = []
    latencies: list[float] = []
    missing = 0

    for answer_id, gold_row in gold.items():
        relevant_raw = gold_row.get("relevant_doc_ids")
        facts_raw = gold_row.get("required_facts")
        if not isinstance(relevant_raw, list) or not relevant_raw:
            raise DatasetError(f"gold id {answer_id!r} requires relevant_doc_ids")
        if not isinstance(facts_raw, list) or not facts_raw:
            raise DatasetError(f"gold id {answer_id!r} requires required_facts")
        relevant = {str(value) for value in relevant_raw}
        answer_row = answers.get(answer_id)
        if answer_row is None:
            missing += 1
            cited: set[str] = set()
            answer_tokens: list[str] = []
        else:
            answer = answer_row.get("answer")
            cited_raw = answer_row.get("cited_doc_ids")
            if not isinstance(answer, str):
                raise DatasetError(f"answer id {answer_id!r} requires answer")
            if not isinstance(cited_raw, list):
                raise DatasetError(f"answer id {answer_id!r} requires cited_doc_ids")
            cited = {str(value) for value in cited_raw}
            answer_tokens = _normalised_tokens(answer)
            latency = _latency_value(answer_row, record_id=answer_id, source="answer")
            if latency is not None:
                latencies.append(latency)

        citation_precisions.append(len(cited & relevant) / len(cited) if cited else 0.0)
        citation_recalls.append(len(cited & relevant) / len(relevant))
        covered = 0
        for fact in facts_raw:
            if not isinstance(fact, str) or not fact.strip():
                raise DatasetError(f"gold id {answer_id!r} requires non-empty string facts")
            fact_tokens = _normalised_tokens(fact)
            covered += int(_contains_token_phrase(answer_tokens, fact_tokens))
        fact_coverages.append(covered / len(facts_raw))

    return {
        "schema_version": "1.0",
        "task": "answer",
        "total": len(gold),
        "missing_answers": missing,
        "citation_precision": mean(citation_precisions),
        "citation_recall": mean(citation_recalls),
        "required_fact_coverage": mean(fact_coverages),
        "latency_ms": {
            "samples": len(latencies),
            "mean": mean(latencies) if latencies else 0.0,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
    }
