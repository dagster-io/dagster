import datetime

import dagster as dg
import pytest
from dagster import AutomationCondition as AC
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
        ("292681bbb584cf9631b69b3fdfa06787", AC.on_cron("0 * * * *"), one_parent, False),
        ("e7910eab13c78e28935517bfca394d91", AC.on_cron("0 * * * *"), one_parent, True),
        ("14d4548a06631a7f476362c8a67eb4ad", AC.on_cron("0 0 * * *"), one_parent, False),
        ("1c04bde0c0f3067d1552dd98e3fc665f", AC.on_cron("0 * * * *"), one_parent_daily, False),
        ("c74035e602a41068712a71ccbc0e770f", AC.on_cron("0 * * * *"), two_parents, False),
        ("5648714437da451d234ca4d5f057ea53", AC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("0cbfe01d98dbab4ad7e0b67d8d866aba", AC.eager(), one_parent, False),
        ("8ed0a6692663a452f1b17a3d416c5a1d", AC.eager(), one_parent, True),
        ("65481f01e42f6b3d6118816b89a6e20c", AC.eager(), one_parent_daily, False),
        (
            # note: identical hash to the above
            "65481f01e42f6b3d6118816b89a6e20c",
            AC.eager().allow(AssetSelection.all()),
            one_parent_daily,
            False,
        ),
        ("ba54c126d578967f5e2c2a396179409c", AC.eager(), two_parents, False),
        ("2c339454ec7cb1282ba669d36fa61ebf", AC.eager(), two_parents_daily, False),
        # missing condition is invariant to changes other than partitions def changes
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), one_parent, False),
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), one_parent, True),
        ("6d7809c4949e3d812d7eddfb1b60d529", AC.missing(), two_parents, False),
        ("7f852ab7408c67e0830530d025505a37", AC.missing(), two_parents_daily, False),
        ("7f852ab7408c67e0830530d025505a37", AC.missing(), one_parent_daily, False),
    ],
)
async def test_value_hash(
    condition: AC, scenario_spec: ScenarioSpec, expected_value_hash: str, materialize_A: bool
) -> None:
    state = AutomationConditionScenarioState(
        scenario_spec, automation_condition=condition
    ).with_current_time("2024-01-01T00:00")

    state, _ = await state.evaluate("downstream")
    if materialize_A:
        state = state.with_runs(run_request("A"))

    state, result = await state.with_current_time("2024-01-01T01:00").evaluate("downstream")
    assert result.value_hash == expected_value_hash


@pytest.mark.parametrize(
    "sequence",
    [
        ["initial", "updated", "updated", "updated", "updated"],
        ["initial", "updated", "initial", "updated", "initial"],
        ["intial", "initial", "initial", "initial", "updated"],
    ],
)
def test_since_condition_memory(sequence: list[str]) -> None:
    downstream_key = dg.AssetKey("downstream")

    @dg.asset
    def u1() -> None: ...

    @dg.asset
    def u2() -> None: ...

    @dg.asset
    def u3() -> None: ...

    condition_initial = AC.on_cron("@hourly")
    # the updated condition buries the original condition in a different layer of the condition tree,
    # but we want to make sure we retain memory of the values. added conditions will not impact
    # the result of the condition (it will always be missing and never failed)
    condition_updated = (condition_initial & AC.missing()) | AC.execution_failed()

    current_time = datetime.datetime(2025, 8, 16, 8, 16, 0)

    @dg.asset(key=downstream_key, deps=[u1, u2, u3], automation_condition=condition_initial)
    def downstream_initial() -> None: ...
    @dg.asset(key=downstream_key, deps=[u1, u2, u3], automation_condition=condition_updated)
    def downstream_updated() -> None: ...

    defs_initial = dg.Definitions(assets=[u1, u2, u3, downstream_initial])
    defs_updated = dg.Definitions(assets=[u1, u2, u3, downstream_updated])

    instance = dg.DagsterInstance.ephemeral()

    # initial baseline evaluation
    result = dg.evaluate_automation_conditions(
        defs_initial, instance=instance, evaluation_time=current_time
    )
    current_time += datetime.timedelta(hours=1)  # pass a cron tick

    # simulate a scenario where we materialize each upstream one by one and then evaluate
    for i, step in enumerate(sequence):
        defs = defs_initial if step == "initial" else defs_updated
        if i in {1, 2, 3}:
            instance.report_runless_asset_event(dg.AssetMaterialization(dg.AssetKey([f"u{i}"])))
        result = dg.evaluate_automation_conditions(
            defs, instance=instance, evaluation_time=current_time, cursor=result.cursor
        )
        # after we request u3, we should request the downstream asset, but the next evaluation
        # afterwards should not request it again
        expected_requested = 1 if i == 3 else 0
        assert result.total_requested == expected_requested


def test_node_unique_id() -> None:
    condition = (
        AC.any_deps_match(AC.missing())
        .allow(AssetSelection.keys("a"))
        .ignore(AssetSelection.keys("b"))
    )
    assert (
        condition.get_node_unique_id(parent_unique_id=None, index=None, target_key=None)
        == "80f87fb32baaf7ce3f65f68c12d3eb11"
    )
    assert condition.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=None, target_key=None
    ) == ["35b152923d1d99348e85c3cbe426bcb7"]
