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


@pytest.mark.parametrize(
    ["expected_value_hash", "condition", "scenario_spec", "materialize_A"],
    [
        # cron condition returns a unique value hash if parents change, if schedule changes, if the
        # partitions def changes, or if an asset is materialized
        ("9a5947c1196f3311a1039aecb90e04f5", SC.on_cron("0 * * * *"), one_parent, False),
        ("bdf32a2d014be85c68843f55776bd70c", SC.on_cron("0 * * * *"), one_parent, True),
        ("be9c8c64a822d0dbc49e462a3aabf4d8", SC.on_cron("0 0 * * *"), one_parent, False),
        ("dfed65a9a20ff1f10e60ff7f0397ffb1", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("44305b43d3719344819f9bda178f4588", SC.on_cron("0 * * * *"), two_parents, False),
        ("1d902e0c59648e5022ae84bd6a1b1c49", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("0e5ef287a89ed9e6c08a25e4920ee4f3", SC.eager(), one_parent, False),
        ("42a1a04bf1fa76fd723fb60294bff6ae", SC.eager(), one_parent, True),
        ("bfb3170339eea63e425d375d2c187c34", SC.eager(), one_parent_daily, False),
        ("0e9b7774d09132a19b8d8674fdca500d", SC.eager(), two_parents, False),
        ("3cf82286c216f9535842fb2852b88838", SC.eager(), two_parents_daily, False),
        # missing condition is invariant to changes other than partitions def changes
        ("5c24ffc21af9983a4917b91290de8f5d", SC.missing(), one_parent, False),
        ("5c24ffc21af9983a4917b91290de8f5d", SC.missing(), one_parent, True),
        ("5c24ffc21af9983a4917b91290de8f5d", SC.missing(), two_parents, False),
        ("c722c1abf97c5f5fe13b2f6fc00af739", SC.missing(), two_parents_daily, False),
        ("c722c1abf97c5f5fe13b2f6fc00af739", SC.missing(), one_parent_daily, False),
    ],
)
def test_value_hash(
    condition: SC, scenario_spec: ScenarioSpec, expected_value_hash: str, materialize_A: bool
) -> None:
    state = AutomationConditionScenarioState(
        scenario_spec, automation_condition=condition
    ).with_current_time("2024-01-01T00:00")

    state, _ = state.evaluate("downstream")
    if materialize_A:
        state = state.with_runs(run_request("A"))

    state, result = state.evaluate("downstream")
    assert result.value_hash == expected_value_hash
