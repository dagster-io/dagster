from dagster._core.definitions.declarative_scheduling.asset_condition import (
    AssetCondition,
)

from ..base_scenario import run_request
from ..scenario_specs import one_asset, two_partitions_def
from .asset_condition_scenario import AssetConditionScenarioState


def test_missing_unpartitioned() -> None:
    state = AssetConditionScenarioState(one_asset, asset_condition=AssetCondition.missing_())

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_runs(run_request("A"))
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_missing_partitioned() -> None:
    state = AssetConditionScenarioState(
        one_asset, asset_condition=AssetCondition.missing_()
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # same partition materialized again
    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state = state.with_runs(run_request("A", "2"))
    _, result = state.evaluate("A")
    assert result.true_subset.size == 0
