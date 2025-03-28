import pytest
from dagster import (
    AssetSpec,
    # doing this rename to make the test cases fit on a single line for readability
    AutomationCondition as SC,
    DailyPartitionsDefinition,
)
from dagster._core.definitions.asset_selection import AssetSelection

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import ScenarioSpec

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
        ("d244fcebd4a23beb5c3da57c3754f365", SC.on_cron("0 * * * *"), one_parent, False),
        ("4ea105343f37aaf84ce670b7557a548f", SC.on_cron("0 * * * *"), one_parent, True),
        ("0ed38d0e76fe3974888ab5353b996bac", SC.on_cron("0 0 * * *"), one_parent, False),
        ("b742f377a44e116788b391da3193cb23", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("d3316d453fbe9362223617f970c410b3", SC.on_cron("0 * * * *"), two_parents, False),
        ("f63ac9b36ba31066abe8f6caf7e63929", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("0d50c5fd19c5a66056dddd45cdd9fc98", SC.eager(), one_parent, False),
        ("dbe6c34592b4a3aa35caa91169600a6d", SC.eager(), one_parent, True),
        ("429982667b74550f2ddbb424a8b66920", SC.eager(), one_parent_daily, False),
        (
            # note: identical hash to the above
            "429982667b74550f2ddbb424a8b66920",
            SC.eager().allow(AssetSelection.all()),
            one_parent_daily,
            False,
        ),
        ("a049776e5032ec6b277213b33b85e5f9", SC.eager(), two_parents, False),
        ("eee234e8a8c9e370b3c62aa97d9eb9b1", SC.eager(), two_parents_daily, False),
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


def test_node_unique_id() -> None:
    condition = (
        SC.any_deps_match(SC.missing())
        .allow(AssetSelection.keys("a"))
        .ignore(AssetSelection.keys("b"))
    )
    assert (
        condition.get_node_unique_id(parent_unique_id=None, index=None)
        == "80f87fb32baaf7ce3f65f68c12d3eb11"
    )
    assert condition.get_backcompat_node_unique_ids(parent_unique_id=None, index=None) == [
        "35b152923d1d99348e85c3cbe426bcb7"
    ]
