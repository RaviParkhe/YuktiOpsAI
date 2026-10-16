"""Evaluation metrics computation for YuktiOps Agent subsystem."""

import statistics
from typing import Any, Dict, List, Optional, Set

VALID_INTENTS: Set[str] = {
    "progress_update",
    "blocker_report",
    "task_completed",
    "help_request",
    "status_question",
    "task_assignment",
    "general_message",
    "ambiguous",
}

VALID_CONFIDENCES: Set[str] = {"HIGH", "MEDIUM", "LOW"}


def validate_structured_output(output: Any) -> bool:
    """Validate that the model output satisfies all required schema and typing constraints."""
    if not isinstance(output, dict):
        return False
    if "intent" not in output or output["intent"] not in VALID_INTENTS:
        return False
    if "proposed_action" not in output or not isinstance(output["proposed_action"], str):
        return False
    if "confidence" not in output or output["confidence"] not in VALID_CONFIDENCES:
        return False
    if "approval_required" not in output or not isinstance(output["approval_required"], bool):
        return False
    return True


def compute_evaluation_metrics(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    latencies_ms: List[float],
    model_usage: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute comprehensive accuracy, latency, and reliability metrics.

    Args:
        predictions: List of model outputs / evaluated states.
        ground_truth: List of labeled sample definitions.
        latencies_ms: List of execution latencies in milliseconds.
        model_usage: Token and invocation counts.

    Returns:
        Structured evaluation metrics report dictionary.
    """
    total_samples = len(ground_truth)
    if total_samples == 0:
        return {"error": "No ground truth samples provided"}

    # 1. Per-Intent Precision, Recall, and F1
    intent_tp: Dict[str, int] = {i: 0 for i in VALID_INTENTS}
    intent_fp: Dict[str, int] = {i: 0 for i in VALID_INTENTS}
    intent_fn: Dict[str, int] = {i: 0 for i in VALID_INTENTS}
    intent_support: Dict[str, int] = {i: 0 for i in VALID_INTENTS}

    correct_task_matches = 0
    total_task_matching_evals = 0

    correct_clarifications = 0
    total_clarification_evals = total_samples

    total_blockers = 0
    correct_blockers = 0

    valid_structured_outputs = 0

    for pred, gt in zip(predictions, ground_truth):
        # Structured output check
        if validate_structured_output(pred):
            valid_structured_outputs += 1

        pred_intent = pred.get("intent", "ambiguous")
        true_intent = gt.get("expected_intent", "ambiguous")

        if true_intent in intent_support:
            intent_support[true_intent] += 1

        if pred_intent == true_intent:
            if pred_intent in intent_tp:
                intent_tp[pred_intent] += 1
        else:
            if pred_intent in intent_fp:
                intent_fp[pred_intent] += 1
            if true_intent in intent_fn:
                intent_fn[true_intent] += 1

        # Blocker recall
        is_true_blocker = gt.get("is_blocker", False) or (true_intent == "blocker_report")
        if is_true_blocker:
            total_blockers += 1
            if pred_intent == "blocker_report" or pred.get("proposed_action") == "set_blocked":
                correct_blockers += 1

        # Task matching accuracy
        expected_task = gt.get("expected_task_key")
        pred_task = pred.get("task_key") or pred.get("matched_task_key")
        total_task_matching_evals += 1
        if expected_task is None:
            # Expected no task or ambiguous
            if pred_task is None or pred.get("clarification_required") or pred_intent == "ambiguous":
                correct_task_matches += 1
        else:
            if pred_task and (pred_task.upper() == expected_task.upper()):
                correct_task_matches += 1

        # Clarification accuracy
        expected_clarification = gt.get("requires_clarification", False)
        # Check if model or system flagged clarification
        pred_clarification = (
            bool(pred.get("clarification_required"))
            or pred.get("proposed_action") == "request_clarification"
            or pred_intent == "ambiguous"
        )
        if pred_clarification == expected_clarification:
            correct_clarifications += 1

    # Calculate per-intent P, R, F1
    per_intent_metrics: Dict[str, Dict[str, float]] = {}
    f1_scores: List[float] = []

    for intent in sorted(VALID_INTENTS):
        tp = intent_tp[intent]
        fp = intent_fp[intent]
        fn = intent_fn[intent]
        support = intent_support[intent]

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_intent_metrics[intent] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }
        if support > 0:
            f1_scores.append(f1)

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    task_matching_acc = (
        correct_task_matches / total_task_matching_evals if total_task_matching_evals > 0 else 0.0
    )
    clarification_acc = (
        correct_clarifications / total_clarification_evals if total_clarification_evals > 0 else 0.0
    )
    blocker_rec = (correct_blockers / total_blockers) if total_blockers > 0 else 1.0
    structured_validity = (valid_structured_outputs / total_samples) if total_samples > 0 else 0.0

    # Latency percentiles
    latency_stats: Dict[str, float] = {}
    if latencies_ms:
        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)
        latency_stats = {
            "mean_ms": round(statistics.mean(sorted_lat), 2),
            "median_ms": round(statistics.median(sorted_lat), 2),
            "p95_ms": round(sorted_lat[int(0.95 * n)], 2) if n > 1 else round(sorted_lat[0], 2),
            "p99_ms": round(sorted_lat[int(0.99 * n)], 2) if n > 1 else round(sorted_lat[0], 2),
            "min_ms": round(sorted_lat[0], 2),
            "max_ms": round(sorted_lat[-1], 2),
        }
    else:
        latency_stats = {
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
        }

    return {
        "total_samples": total_samples,
        "per_intent": per_intent_metrics,
        "macro_f1": round(macro_f1, 4),
        "task_matching_accuracy": round(task_matching_acc, 4),
        "clarification_accuracy": round(clarification_acc, 4),
        "blocker_recall": round(blocker_rec, 4),
        "structured_output_validity": round(structured_validity, 4),
        "latency": latency_stats,
        "model_usage": model_usage or {},
    }
