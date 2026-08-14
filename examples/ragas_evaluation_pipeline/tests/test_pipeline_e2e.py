"""End-to-end materialization test for the 8-asset graph (Step 12)."""

from typing import cast

from dagster import AssetsDefinition, DagsterInstance, load_assets_from_modules, materialize
from ragas_evaluation_pipeline.assets import pipeline
from ragas_evaluation_pipeline.resources.runtime_metadata_resource import RuntimeMetadataResource

_EXPECTED_ASSETS = {
    "evaluation_dataset_asset",
    "retrieved_contexts_asset",
    "generated_answers_asset",
    "retrieval_metric_results_asset",
    "generation_metric_results_asset",
    "combined_metric_results_asset",
    "regression_comparison_asset",
    "run_summary_asset",
}


def _eval_assets() -> list[AssetsDefinition]:
    """Load the pipeline assets, cast for the type checker (all are AssetsDefinition)."""
    return cast("list[AssetsDefinition]", load_assets_from_modules([pipeline]))


def test_full_graph_materializes_in_deterministic_mode():
    result = materialize(_eval_assets(), resources={"runtime_metadata": RuntimeMetadataResource()})
    assert result.success

    materialized = {
        ev.asset_key.to_user_string()
        for ev in result.get_asset_materialization_events()
        if ev.asset_key is not None
    }
    assert _EXPECTED_ASSETS <= materialized

    combined = cast("dict", result.output_for_node("combined_metric_results_asset"))
    assert set(combined) == {"retrieval", "generation"}
    for group in combined.values():
        assert all(0.0 <= v <= 1.0 for v in group.values())


def test_retrieval_and_generation_metrics_are_separated():
    """Point 5: retrieval vs generation live in distinct assets/keys."""
    result = materialize(_eval_assets(), resources={"runtime_metadata": RuntimeMetadataResource()})
    ret = cast("dict", result.output_for_node("retrieval_metric_results_asset"))["aggregate"]
    gen = cast("dict", result.output_for_node("generation_metric_results_asset"))["aggregate"]
    assert "context_recall" in ret and "faithfulness" not in ret
    assert "faithfulness" in gen and "context_recall" not in gen


def test_regression_uses_checked_in_baseline_on_first_run():
    """Point 6: with no prior materialization, fall back to the baseline file."""
    with DagsterInstance.ephemeral() as instance:
        result = materialize(
            _eval_assets(),
            resources={"runtime_metadata": RuntimeMetadataResource()},
            instance=instance,
        )
        assert result.success
        regression = cast("dict", result.output_for_node("regression_comparison_asset"))
        assert regression["baseline_source"] == "checked_in_baseline"


def test_lineage_metadata_is_emitted_on_combined_asset():
    """Point 7: the combined asset stamps every lineage/reproducibility tag.

    This is the headline "evidence" feature — assert the tags are actually
    attached to the materialization, not just that the run succeeds.
    """
    result = materialize(_eval_assets(), resources={"runtime_metadata": RuntimeMetadataResource()})
    assert result.success

    mats = result.asset_materializations_for_node("combined_metric_results_asset")
    metadata_keys = set(mats[0].metadata.keys())

    expected_tags = {
        "model_name",
        "embedding_model",
        "index_version",
        "prompt_version",
        "corpus_hash",
        "dataset_id",
        "dataset_semver",
    }
    assert expected_tags <= metadata_keys, expected_tags - metadata_keys
    # corpus_hash is the 12-char content fingerprint, not an empty placeholder.
    corpus_hash = mats[0].metadata["corpus_hash"].value
    assert isinstance(corpus_hash, str) and len(corpus_hash) == 12


def test_regression_compares_against_previous_materialization():
    """Point 6: a second run diffs against the first run's materialized result."""
    with DagsterInstance.ephemeral() as instance:
        first = materialize(
            _eval_assets(),
            resources={"runtime_metadata": RuntimeMetadataResource()},
            instance=instance,
        )
        assert first.success

        second = materialize(
            _eval_assets(),
            resources={"runtime_metadata": RuntimeMetadataResource()},
            instance=instance,
        )
        assert second.success

        regression = cast("dict", second.output_for_node("regression_comparison_asset"))
        assert regression["baseline_source"] == "previous_materialization"
        # The baseline it diffed against is the FIRST run, not the current one.
        assert regression["baseline_run_id"] == first.run_id
        assert regression["baseline_run_id"] != second.run_id


def test_regression_skips_incompatible_checked_in_baseline_fallback():
    """A reconfigured or RAGAS run must skip regression comparison instead of fabricating deltas."""
    with DagsterInstance.ephemeral() as instance:
        result = materialize(
            _eval_assets(),
            resources={"runtime_metadata": RuntimeMetadataResource(scorer="ragas")},
            instance=instance,
        )
        assert result.success

        regression = cast("dict", result.output_for_node("regression_comparison_asset"))
        assert regression["baseline_source"] == "no_compatible_baseline"
        assert regression["baseline_run_id"] is None
        assert regression["deltas"] == {}
