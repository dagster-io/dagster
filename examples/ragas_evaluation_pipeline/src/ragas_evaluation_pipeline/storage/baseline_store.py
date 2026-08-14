"""Baseline resolution for the regression comparison (Point 6).

The regression asset compares the current run against the **previous materialized
evaluation result**, read back from the Dagster instance's event log
(:func:`load_previous_metrics`). On a clean instance — the very first run, or a
fresh checkout in CI — there is no prior materialization, so it falls back to the
checked-in baseline file ``data/baseline_metrics.json`` (:func:`load_baseline`).

That fallback is what keeps the example runnable offline with no history, while
the primary path is a true run-over-run lineage comparison.
"""

from __future__ import annotations

import json

from ragas_evaluation_pipeline.config import BASELINE_PATH

# Asset whose materialization metadata carries the metric values we diff against.
COMBINED_ASSET_KEY = "combined_metric_results_asset"


def load_baseline() -> dict:
    """Read the checked-in baseline metrics file (first-run / no-history fallback)."""
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def load_previous_metrics(instance, current_run_id: str | None) -> dict | None:
    """Return the previous run's combined metrics from the instance event log.

    Reads back the ``retrieval``/``generation`` JSON metadata attached to the most
    recent ``combined_metric_results_asset`` materialization that did **not** come
    from the current run (the current run's own materialization already exists in
    the log by the time the regression asset runs, so it must be skipped).

    Returns a dict shaped like the baseline file
    (``{"retrieval": {...}, "generation": {...}, "baseline_run_id": ...}``) or
    ``None`` when there is no usable prior materialization.
    """
    from dagster import AssetKey

    result = instance.fetch_materializations(
        AssetKey(COMBINED_ASSET_KEY), limit=25
    )  # most-recent-first
    for record in result.records:
        entry = record.event_log_entry
        if entry.run_id == current_run_id:
            continue  # skip this run's own materialization
        materialization = entry.asset_materialization
        if materialization is None:
            continue
        metadata = materialization.metadata
        if "retrieval" not in metadata or "generation" not in metadata:
            continue
        try:
            return {
                "retrieval": dict(metadata["retrieval"].value),
                "generation": dict(metadata["generation"].value),
                "baseline_run_id": entry.run_id,
            }
        except (AttributeError, TypeError, ValueError):
            continue  # unexpected metadata shape — try the next record
    return None


def flatten_metrics(metrics: dict) -> dict:
    """Flatten {"retrieval": {...}, "generation": {...}} into one metric->value map.

    Works for both the baseline file and the combined_metric_results_asset value,
    since they share the same retrieval/generation shape.
    """
    flat: dict = {}
    for group in ("retrieval", "generation"):
        for name, value in metrics.get(group, {}).items():
            if isinstance(value, (int, float)):
                flat[name] = float(value)
    return flat
