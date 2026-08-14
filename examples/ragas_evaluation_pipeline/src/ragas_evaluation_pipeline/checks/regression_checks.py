"""Regression tolerance asset check (Point 6).

Compares current per-metric scores against the checked-in baseline and fails if
any required metric drops by more than config.REGRESSION_TOLERANCE. The deltas
themselves are computed in regression_comparison_asset; this check enforces the
policy on them.
"""

from dagster import AssetCheckResult, MetadataValue, asset_check

from ragas_evaluation_pipeline.config import REGRESSION_TOLERANCE


@asset_check(asset="regression_comparison_asset")
def regression_tolerance_check(regression_comparison_asset: dict) -> AssetCheckResult:
    """Fail if the worst per-metric drop exceeds the allowed tolerance."""
    deltas = regression_comparison_asset["deltas"]
    if deltas:
        worst_metric = min(deltas, key=deltas.get)
        worst_delta = deltas[worst_metric]
    else:
        worst_metric, worst_delta = None, 0.0

    passed = worst_delta >= -REGRESSION_TOLERANCE
    return AssetCheckResult(
        passed=passed,
        metadata={
            "worst_metric": str(worst_metric),
            "worst_delta": worst_delta,
            "tolerance": -REGRESSION_TOLERANCE,
            "deltas": MetadataValue.json(deltas),
        },
    )


regression_checks = [regression_tolerance_check]
