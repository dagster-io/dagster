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
        ("0696dcb07b82fd8f4934c828bbc8365f", SC.on_cron("0 * * * *"), one_parent, False),
        ("7fb8a01606b51f6306e85769533fd5b9", SC.on_cron("0 * * * *"), one_parent, True),
        ("38ba78431e6c22552840e7177918a880", SC.on_cron("0 0 * * *"), one_parent, False),
        ("98e74cd660564cb881d889ec9ae75ce0", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("c0e6323656d8208666e8c74d9af93a64", SC.on_cron("0 * * * *"), two_parents, False),
        ("3545889e64a11959400cb116ba2320ec", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("65f04b97a21501e043b8f3468dbe1b0d", SC.eager(), one_parent, False),
        ("f05bc0e375b310db37e7440b7a19c5b0", SC.eager(), one_parent, True),
        ("9ac1d99f9f0ce0e75a4de15f56791aea", SC.eager(), one_parent_daily, False),
        ("16c84b631ff46a4cd1c44b8772f015d7", SC.eager(), two_parents, False),
        ("bbfa1e36a49aad4c955f9d2536529093", SC.eager(), two_parents_daily, False),
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
