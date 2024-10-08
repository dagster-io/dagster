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
        ("ad228f0044da1efba407e794c845e858", SC.on_cron("0 * * * *"), one_parent, False),
        ("f34de3cd3e1ab283a95a892192437076", SC.on_cron("0 * * * *"), one_parent, True),
        ("d9533b4eb0aad1798d5da85520b9852c", SC.on_cron("0 0 * * *"), one_parent, False),
        ("8a233d38e569faba1470b0717c28fbee", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("e8fa53c550e99edc1346a1f80979cddd", SC.on_cron("0 * * * *"), two_parents, False),
        ("5c58fb8fc117d69b32e734c45af219ea", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("678e0a2be6bba89bd2d37fb432d8fb51", SC.eager(), one_parent, False),
        ("72bd068363441e02d67b3407fe3e9cae", SC.eager(), one_parent, True),
        ("4f0e2e38131ae91b1b9408e3cd549dd0", SC.eager(), one_parent_daily, False),
        ("00ecedd77a8d887940856950c556c7d1", SC.eager(), two_parents, False),
        ("6ad1fd331c63c75e17572ec60b9c27b5", SC.eager(), two_parents_daily, False),
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
