import pytest
from dagster import (
    AssetSpec,
    # doing this rename to make the test cases fit on a single line for readability
    AutomationCondition as SC,
    DailyPartitionsDefinition,
)

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    run_request,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    ScenarioSpec,
)

one_parent = ScenarioSpec(asset_specs=[AssetSpec("A"), AssetSpec("downstream", deps=["A"])])
two_parents = ScenarioSpec(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("downstream", deps=["A", "B"])]
)

daily_partitions = DailyPartitionsDefinition(start_date="2020-01-01")
one_parent_daily = one_parent.with_asset_properties(partitions_def=daily_partitions)
two_parents_daily = two_parents.with_asset_properties(partitions_def=daily_partitions)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["expected_value_hash", "condition", "scenario_spec", "materialize_A"],
    [
        # cron condition returns a unique value hash if parents change, if schedule changes, if the
        # partitions def changes, or if an asset is materialized
        ("93831bb3ab9c6ef4b10a7f823ce5cc1f", SC.on_cron("0 * * * *"), one_parent, False),
        ("97ea4d62fcef2f6a2ecc99a95d5c1769", SC.on_cron("0 * * * *"), one_parent, True),
        ("504192a87594854d3964bb03e2092394", SC.on_cron("0 0 * * *"), one_parent, False),
        ("ccbd282bf8e6d711c2bb0e01ebb16728", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("dd74c7cfe19d869931ea4aad9ee10127", SC.on_cron("0 * * * *"), two_parents, False),
        ("861f8e40d4624d49c4ebdd034c8e1e84", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("9b4c0a55b5fbea860f72ecc9d7a27e0e", SC.eager(), one_parent, False),
        ("6925b7770eb2122048e4f50aa0a3303f", SC.eager(), one_parent, True),
        ("45c2493882264dd06bee6c9abffabf3e", SC.eager(), one_parent_daily, False),
        ("81132ce4972e8ac8d8be1a0e468637c0", SC.eager(), two_parents, False),
        ("724d21fef8f7404f1e26b40ddeab711d", SC.eager(), two_parents_daily, False),
        # missing condition is invariant to changes other than partitions def changes
        ("6d7809c4949e3d812d7eddfb1b60d529", SC.missing(), one_parent, False),
        ("6d7809c4949e3d812d7eddfb1b60d529", SC.missing(), one_parent, True),
        ("6d7809c4949e3d812d7eddfb1b60d529", SC.missing(), two_parents, False),
        ("7f852ab7408c67e0830530d025505a37", SC.missing(), two_parents_daily, False),
        ("7f852ab7408c67e0830530d025505a37", SC.missing(), one_parent_daily, False),
    ],
)
async def test_value_hash(
    condition: SC, scenario_spec: ScenarioSpec, expected_value_hash: str, materialize_A: bool
) -> None:
    state = AutomationConditionScenarioState(
        scenario_spec, automation_condition=condition
    ).with_current_time("2024-01-01T00:00")

    state, _ = await state.evaluate("downstream")
    if materialize_A:
        state = state.with_runs(run_request("A"))

    state, result = await state.evaluate("downstream")
    assert result.value_hash == expected_value_hash
