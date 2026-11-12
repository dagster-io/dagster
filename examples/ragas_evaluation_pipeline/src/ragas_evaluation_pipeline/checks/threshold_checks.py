"""Absolute threshold asset checks — the release gate (Point 3).

  - faithfulness       >= FAITHFULNESS_MIN
  - answer_relevancy   >= ANSWER_RELEVANCY_MIN
  - answer_correctness >= ANSWER_CORRECTNESS_MIN   (right-doc/wrong-sentence guard)
  - context_recall     >= CONTEXT_RECALL_MIN
  - citation_coverage  >= baseline
  - one aggregate release_gate_check that fails if any required check fails,
    surfacing the failing metric details in the check result metadata.

Thresholds are defined in :mod:`..config`.
"""

from dagster import AssetCheckResult, MetadataValue, asset_check

from ragas_evaluation_pipeline.config import (
    ANSWER_CORRECTNESS_MIN,
    ANSWER_RELEVANCY_MIN,
    CONTEXT_RECALL_MIN,
    FAITHFULNESS_MIN,
)
from ragas_evaluation_pipeline.storage.baseline_store import flatten_metrics, load_baseline

_ASSET = "combined_metric_results_asset"


def _threshold_result(value: float, threshold: float) -> AssetCheckResult:
    """Standard pass/fail result carrying the value + threshold as evidence."""
    return AssetCheckResult(
        passed=value >= threshold,
        metadata={"value": value, "threshold": threshold, "margin": round(value - threshold, 4)},
    )


@asset_check(asset=_ASSET)
def faithfulness_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    return _threshold_result(
        combined_metric_results_asset["generation"]["faithfulness"], FAITHFULNESS_MIN
    )


@asset_check(asset=_ASSET)
def answer_relevancy_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    return _threshold_result(
        combined_metric_results_asset["generation"]["answer_relevancy"],
        ANSWER_RELEVANCY_MIN,
    )


@asset_check(asset=_ASSET)
def answer_correctness_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    return _threshold_result(
        combined_metric_results_asset["generation"]["answer_correctness"],
        ANSWER_CORRECTNESS_MIN,
    )


@asset_check(asset=_ASSET)
def context_recall_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    return _threshold_result(
        combined_metric_results_asset["retrieval"]["context_recall"], CONTEXT_RECALL_MIN
    )


@asset_check(asset=_ASSET)
def citation_coverage_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    """Citation coverage must not drop below the recorded baseline value."""
    baseline = flatten_metrics(load_baseline())
    threshold = baseline.get("citation_coverage", 0.0)
    return _threshold_result(
        combined_metric_results_asset["retrieval"]["citation_coverage"], threshold
    )


def evaluate_release_gate(combined: dict, baseline: dict) -> tuple[bool, dict]:
    """Pure release-gate decision (kept separate so it is unit-testable).

    Returns ``(passed, failing)`` where ``failing`` maps each metric that missed
    its threshold to its value + threshold.
    """
    gen = combined["generation"]
    ret = combined["retrieval"]
    gates = {
        "faithfulness": (gen["faithfulness"], FAITHFULNESS_MIN),
        "answer_relevancy": (gen["answer_relevancy"], ANSWER_RELEVANCY_MIN),
        "answer_correctness": (gen["answer_correctness"], ANSWER_CORRECTNESS_MIN),
        "context_recall": (ret["context_recall"], CONTEXT_RECALL_MIN),
        "citation_coverage": (ret["citation_coverage"], baseline.get("citation_coverage", 0.0)),
    }
    failing = {
        metric: {"value": value, "threshold": threshold}
        for metric, (value, threshold) in gates.items()
        if value < threshold
    }
    return (not failing, failing)


@asset_check(asset=_ASSET)
def release_gate_check(combined_metric_results_asset: dict) -> AssetCheckResult:
    """Aggregate gate: fails if ANY required metric misses its threshold.

    Surfaces every failing metric (value + threshold) so the release decision is
    self-explaining in the Dagster UI.
    """
    passed, failing = evaluate_release_gate(
        combined_metric_results_asset, flatten_metrics(load_baseline())
    )
    return AssetCheckResult(
        passed=passed,
        metadata={
            "decision": "PASS" if passed else "FAIL",
            "failing_metrics": MetadataValue.json(failing),
            "num_failing": len(failing),
        },
    )


threshold_checks = [
    faithfulness_check,
    answer_relevancy_check,
    answer_correctness_check,
    context_recall_check,
    citation_coverage_check,
    release_gate_check,
]
