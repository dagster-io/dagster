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
        ("b965fde7adb65aefeaceccb72d1924f7", SC.on_cron("0 * * * *"), one_parent, False),
        ("455fa56d35fd9ae07bc9ee891ea109d7", SC.on_cron("0 * * * *"), one_parent, True),
        ("e038e2ffef6417fe048dbdb927b56fdf", SC.on_cron("0 0 * * *"), one_parent, False),
        ("bf862feb81bc2f90c0c4e9ba1ef21722", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("0179e633e3c1aac0d7af0dd3a3889f1a", SC.on_cron("0 * * * *"), two_parents, False),
        ("4fdc71aabbed73dea6c00791888592fa", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("c805f615f8fad6c62921b2193c1f60d5", SC.eager(), one_parent, False),
        ("71cb14a01a9088dff3d493a6aaa0aa12", SC.eager(), one_parent, True),
        ("254c20541b0d06a0bfb05847640bb94a", SC.eager(), one_parent_daily, False),
        ("f22b09588931194eb224c3efa08e43dc", SC.eager(), two_parents, False),
        ("c02ffb6e7fc44bbdd2f999e37dc3618c", SC.eager(), two_parents_daily, False),
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
