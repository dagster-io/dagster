import pytest
from dagster import (
    AssetSpec,
    DailyPartitionsDefinition,
    # doing this rename to make the test cases fit on a single line for readability
    SchedulingCondition as SC,
)

from dagster_tests.definitions_tests.auto_materialize_tests.base_scenario import run_request

from ..scenario_specs import ScenarioSpec
from .asset_condition_scenario import SchedulingConditionScenarioState

one_parent = ScenarioSpec(asset_specs=[AssetSpec("A"), AssetSpec("downstream", deps=["A"])])
two_parents = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("downstream", deps=["A", "B"])]
)

daily_partitions = DailyPartitionsDefinition(start_date="2020-01-01")
one_parent_daily = one_parent.with_asset_properties(partitions_def=daily_partitions)
two_parents_daily = two_parents.with_asset_properties(partitions_def=daily_partitions)


@pytest.mark.parametrize(
    ["expected_value_hash", "condition", "scenario_spec", "materialize_A"],
    [
        # cron condition returns a unique value hash if parents change, if schedule changes, if the
        # partitions def changes, or if an asset is materialized
        ("a92dbabace17f6e01d1401b24fa8ef91", SC.on_cron("0 * * * *"), one_parent, False),
        ("e05365738d0ab47ba9f7b190caa29937", SC.on_cron("0 * * * *"), one_parent, True),
        ("64bbf6ecddf773acb296d3e2e46dc0f8", SC.on_cron("0 0 * * *"), one_parent, False),
        ("949c0ff067cc0bd50ca162d0fbbc345b", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("f6655af0492e256b4abd3f1cde6bf7c9", SC.on_cron("0 * * * *"), two_parents, False),
        ("71a75f6029a963e6336bc611f1c23dde", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("f2c737a2ae995a3ef9b7de145a41f249", SC.eager(), one_parent, False),
        ("696704072f276a082ce065681d167b5f", SC.eager(), one_parent, True),
        ("0cff09ea2ac9ee4472c2bb42a5be61f0", SC.eager(), one_parent_daily, False),
        ("6089616e33622bf574cc2c273b9e2de1", SC.eager(), two_parents, False),
        ("6306aac109c81f251b9cf731da5a0146", SC.eager(), two_parents_daily, False),
        # missing condition is invariant to changes other than partitions def changes
        ("707c5cea910e6dc1694cb6c388de9177", SC.missing(), one_parent, False),
        ("707c5cea910e6dc1694cb6c388de9177", SC.missing(), one_parent, True),
        ("707c5cea910e6dc1694cb6c388de9177", SC.missing(), two_parents, False),
        ("18766936401c96c0b298b293bfdbde1e", SC.missing(), two_parents_daily, False),
        ("18766936401c96c0b298b293bfdbde1e", SC.missing(), one_parent_daily, False),
    ],
)
def test_value_hash(
    condition: SC, scenario_spec: ScenarioSpec, expected_value_hash: str, materialize_A: bool
) -> None:
    state = SchedulingConditionScenarioState(
        scenario_spec, scheduling_condition=condition
    ).with_current_time("2024-01-01")

    state, _ = state.evaluate("downstream")
    if materialize_A:
        state = state.with_runs(run_request("A"))

    state, result = state.evaluate("downstream")
    assert result.value_hash == expected_value_hash
