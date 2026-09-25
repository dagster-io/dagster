"""Asset-check tests: release-gate + regression logic and full-run green (Step 12)."""

from dagster import AssetSelection, Definitions, define_asset_job, load_assets_from_modules
from ragas_evaluation_pipeline.assets import pipeline
from ragas_evaluation_pipeline.checks import regression_checks, threshold_checks
from ragas_evaluation_pipeline.checks.threshold_checks import evaluate_release_gate
from ragas_evaluation_pipeline.resources.runtime_metadata_resource import RuntimeMetadataResource

_PASSING = {
    "retrieval": {"context_recall": 1.0, "citation_coverage": 1.0},
    "generation": {"faithfulness": 1.0, "answer_relevancy": 1.0, "answer_correctness": 1.0},
}
_BASELINE = {"citation_coverage": 1.0}


def test_release_gate_passes_when_all_metrics_meet_thresholds():
    passed, failing = evaluate_release_gate(_PASSING, _BASELINE)
    assert passed is True
    assert failing == {}


def test_release_gate_fails_and_names_the_offending_metric():
    bad = {
        "retrieval": _PASSING["retrieval"],
        "generation": {**_PASSING["generation"], "faithfulness": 0.10},
    }
    passed, failing = evaluate_release_gate(bad, _BASELINE)
    assert passed is False
    assert "faithfulness" in failing
    assert failing["faithfulness"]["value"] == 0.10


def test_all_checks_pass_on_full_run():
    defs = Definitions(
        assets=load_assets_from_modules([pipeline]),
        asset_checks=[
            *threshold_checks.threshold_checks,
            *regression_checks.regression_checks,
        ],
        jobs=[define_asset_job("eval_job", selection=AssetSelection.all())],
        resources={"runtime_metadata": RuntimeMetadataResource()},
    )
    result = defs.resolve_job_def("eval_job").execute_in_process(raise_on_error=False)
    evals = result.get_asset_check_evaluations()
    assert len(evals) == 7
    assert all(e.passed for e in evals), [e.check_name for e in evals if not e.passed]
