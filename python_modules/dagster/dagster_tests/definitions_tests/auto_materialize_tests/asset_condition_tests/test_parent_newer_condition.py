from dagster import SchedulingCondition

from ..base_scenario import run_request
from ..scenario_specs import one_asset_depends_on_two, two_partitions_def
from .asset_condition_scenario import SchedulingConditionScenarioState


def test_parent_newer_unpartitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset_depends_on_two, scheduling_condition=SchedulingCondition.parent_newer()
    )

    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # now C is refreshed, so no longer any newer parents
    state = state.with_runs(run_request("C"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    # B and C updated -> C still newer
    state = state.with_runs(run_request("B"))
    state = state.with_runs(run_request("C"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    # C and B updated -> now B is newer
    state = state.with_runs(run_request("C"))
    state = state.with_runs(run_request("B"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # recalculate from scratch, B is still newer
    state = state.without_cursor()
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1


def test_parent_newer_partitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset_depends_on_two, scheduling_condition=SchedulingCondition.parent_newer()
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # same partition materialized again
    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # different partition materialized, still upstream of C 1
    state = state.with_runs(run_request("B", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # C 2 upstream materialized
    state = state.with_runs(run_request("B", "2"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 2

    # C 1 materialized, only C 2 has a newer parent
    state = state.with_runs(run_request("C", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # B 1, C 1 materialized, only C 2 has a newer parent
    state = state.with_runs(run_request("B", "1"))
    state = state.with_runs(run_request("C", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # C 1, B 1 materialized, both have newer parents
    state = state.with_runs(run_request("C", "1"))
    state = state.with_runs(run_request("B", "1"))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 2

    # recalculate from scratch, both still have newer parents
    state = state.without_cursor()
    state, result = state.evaluate("C")
    assert result.true_subset.size == 2
