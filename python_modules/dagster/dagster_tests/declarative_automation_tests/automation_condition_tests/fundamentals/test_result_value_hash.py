import dagster as dg
import pytest
from dagster import AutomationCondition as SC
from dagster._core.definitions.asset_selection import AssetSelection

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import ScenarioSpec

one_parent = ScenarioSpec(asset_specs=[dg.AssetSpec("A"), dg.AssetSpec("downstream", deps=["A"])])
two_parents = ScenarioSpec(
    asset_specs=[dg.AssetSpec("A"), dg.AssetSpec("B"), dg.AssetSpec("downstream", deps=["A", "B"])]
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2020-01-01")
one_parent_daily = one_parent.with_asset_properties(partitions_def=daily_partitions)
two_parents_daily = two_parents.with_asset_properties(partitions_def=daily_partitions)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["expected_value_hash", "condition", "scenario_spec", "materialize_A"],
    [
        # cron condition returns a unique value hash if parents change, if schedule changes, if the
        # partitions def changes, or if an asset is materialized
        ("292681bbb584cf9631b69b3fdfa06787", SC.on_cron("0 * * * *"), one_parent, False),
        ("e7910eab13c78e28935517bfca394d91", SC.on_cron("0 * * * *"), one_parent, True),
        ("14d4548a06631a7f476362c8a67eb4ad", SC.on_cron("0 0 * * *"), one_parent, False),
        ("1c04bde0c0f3067d1552dd98e3fc665f", SC.on_cron("0 * * * *"), one_parent_daily, False),
        ("c74035e602a41068712a71ccbc0e770f", SC.on_cron("0 * * * *"), two_parents, False),
        ("5648714437da451d234ca4d5f057ea53", SC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("0cbfe01d98dbab4ad7e0b67d8d866aba", SC.eager(), one_parent, False),
        ("8ed0a6692663a452f1b17a3d416c5a1d", SC.eager(), one_parent, True),
        ("65481f01e42f6b3d6118816b89a6e20c", SC.eager(), one_parent_daily, False),
        (
            # note: identical hash to the above
            "65481f01e42f6b3d6118816b89a6e20c",
            SC.eager().allow(AssetSelection.all()),
            one_parent_daily,
            False,
        ),
        ("ba54c126d578967f5e2c2a396179409c", SC.eager(), two_parents, False),
        ("2c339454ec7cb1282ba669d36fa61ebf", SC.eager(), two_parents_daily, False),
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

    state, result = await state.with_current_time("2024-01-01T01:00").evaluate("downstream")
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
