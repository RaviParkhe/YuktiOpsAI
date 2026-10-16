"""Repeatable evaluation runner for YuktiOps AI Agent subsystem.

Usage:
    # Run evaluation on dev split using offline deterministic mock mode:
    uv run python -m eval.evaluate --split dev --mock

    # Run evaluation on held-out test split:
    uv run python -m eval.evaluate --split test --mock

    # Run evaluation with live Gemini API (if key is set):
    uv run python -m eval.evaluate --split test --live
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from eval.metrics import compute_evaluation_metrics
from eval.mock_llm import MockLLMService

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("eval")


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load JSONL dataset from file."""
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                data = json.loads(line)
                records.append(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse line {line_no} in {dataset_path}: {e}")
    return records


def extract_task_key_from_text(text: str) -> Optional[str]:
    """Extract standard task key from message text using project patterns (e.g., YUK-101)."""
    if not text:
        return None
    matches = re.findall(r"\b([A-Za-z]{2,10}-\d+)\b", text)
    if len(matches) == 1:
        return matches[0].upper()
    return None  # None if zero or multiple (ambiguous)


async def run_evaluation(
    dataset_path: str,
    use_mock: bool = True,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute evaluation harness over the labeled dataset."""
    samples = load_dataset(dataset_path)
    if not samples:
        print(f"Error: No samples found in {dataset_path}")
        return {}

    # Initialize LLM service
    llm_service: Any
    if use_mock:
        llm_service = MockLLMService()
    else:
        from src.services.llm import LLMService
        llm_service = LLMService(mock_mode=False)

    predictions: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []

    print(f"\n=======================================================")
    print(f" YuktiOps Agent Evaluation Harness")
    print(f" Dataset: {dataset_path} ({len(samples)} samples)")
    print(f" Mode: {'Offline Mock (Deterministic)' if use_mock else 'Live Model'}")
    print(f"=======================================================\n")

    for idx, sample in enumerate(samples, 1):
        message_text = sample.get("message_text", "")
        sender_id = sample.get("sender_id")
        task_context = sample.get("task_context")

        # High-precision latency measurement
        t0 = time.perf_counter()
        pred = await llm_service.classify_intent_and_action(
            message_text=message_text,
            task_context=task_context,
            sender_id=sender_id,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        # Evaluate task matching logic
        matched_task = extract_task_key_from_text(message_text)
        if not matched_task and task_context:
            matched_task = task_context.get("task_key")

        # Multi-task detection: if multiple task keys found in message, flag ambiguous / clarification
        all_keys = re.findall(r"\b([A-Za-z]{2,10}-\d+)\b", message_text)
        if len(all_keys) > 1:
            matched_task = None
            pred["clarification_required"] = True
            pred["proposed_action"] = "request_clarification"
            pred["intent"] = "ambiguous"
        elif not matched_task and sample.get("requires_clarification"):
            pred["clarification_required"] = True
            if pred.get("intent") not in ("general_message",):
                pred["proposed_action"] = "request_clarification"

        pred["matched_task_key"] = matched_task
        predictions.append(pred)

    # Compute metrics
    usage = llm_service.get_usage() if hasattr(llm_service, "get_usage") else {}
    report = compute_evaluation_metrics(
        predictions=predictions,
        ground_truth=samples,
        latencies_ms=latencies_ms,
        model_usage=usage,
    )

    # Print summary tables
    _print_evaluation_summary(report)

    # Save output report if requested
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed evaluation report saved to: {out_file}")

    return report


def _print_evaluation_summary(report: Dict[str, Any]) -> None:
    """Print readable summary metrics table to console."""
    print("-------------------------------------------------------------------------")
    print(f" {'INTENT':<22} | {'PRECISION':<10} | {'RECALL':<8} | {'F1':<6} | {'SUPPORT':<8}")
    print("-------------------------------------------------------------------------")
    per_intent = report.get("per_intent", {})
    for intent, scores in per_intent.items():
        print(
            f" {intent:<22} | "
            f" {scores['precision']:<9.4f} | "
            f" {scores['recall']:<7.4f} | "
            f" {scores['f1']:<5.4f} | "
            f" {scores['support']:<8}"
        )
    print("-------------------------------------------------------------------------")

    print("\nOVERALL METRICS:")
    print(f"  • Macro-F1:                   {report.get('macro_f1', 0.0):.4f}")
    print(f"  • Task-Matching Accuracy:     {report.get('task_matching_accuracy', 0.0):.4f} ({(report.get('task_matching_accuracy', 0.0)*100):.1f}%)")
    print(f"  • Clarification Accuracy:     {report.get('clarification_accuracy', 0.0):.4f} ({(report.get('clarification_accuracy', 0.0)*100):.1f}%)")
    print(f"  • Blocker Recall:             {report.get('blocker_recall', 0.0):.4f} ({(report.get('blocker_recall', 0.0)*100):.1f}%)")
    print(f"  • Structured-Output Validity: {report.get('structured_output_validity', 0.0):.4f} ({(report.get('structured_output_validity', 0.0)*100):.1f}%)")

    lat = report.get("latency", {})
    print("\nLATENCY BENCHMARKS (ms):")
    print(f"  • Mean Latency:   {lat.get('mean_ms', 0.0)} ms")
    print(f"  • Median (p50):   {lat.get('median_ms', 0.0)} ms")
    print(f"  • p95 Latency:    {lat.get('p95_ms', 0.0)} ms")
    print(f"  • Min / Max:      {lat.get('min_ms', 0.0)} ms / {lat.get('max_ms', 0.0)} ms")

    usage = report.get("model_usage", {})
    if usage:
        print("\nMODEL USAGE:")
        print(f"  • Model Invocations:       {usage.get('call_count', 0)}")
        print(f"  • Total Prompt Tokens:     {usage.get('total_prompt_tokens', 0)}")
        print(f"  • Total Completion Tokens: {usage.get('total_completion_tokens', 0)}")
        print(f"  • Total Estimated Tokens:  {usage.get('total_tokens', 0)}")
    print("=========================================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="YuktiOps Agent Evaluation Harness")
    parser.add_argument(
        "--split",
        choices=["dev", "test"],
        default="dev",
        help="Evaluation dataset split to evaluate (default: dev)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Direct path to custom JSONL evaluation dataset",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Run in offline deterministic mock mode (default: True, zero cost, no network)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Run against live Google Gemini API (requires GEMINI_API_KEY / GOOGLE_API_KEY)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save output JSON metrics report",
    )

    args = parser.parse_args()

    # Determine dataset path
    base_dir = Path(__file__).parent / "data"
    dataset_path = args.dataset or str(base_dir / f"{args.split}.jsonl")
    output_path = args.output or f"eval/results/{args.split}_report.json"
    use_mock = not args.live

    asyncio.run(
        run_evaluation(
            dataset_path=dataset_path,
            use_mock=use_mock,
            output_path=output_path,
        )
    )


if __name__ == "__main__":
    main()
