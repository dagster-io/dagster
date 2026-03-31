import datetime

import dagster as dg
import pytest
from dagster import AutomationCondition as AC
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._utils.security import non_secure_md5_hash_str

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
        ("e1eb2dcf84a24c4f8b0e328174eb6f82", AC.on_cron("0 * * * *"), one_parent, False),
        ("c70a6e0116190dd47c63eb7ed571c30f", AC.on_cron("0 * * * *"), one_parent, True),
        ("53c9bd094776a1293972551b9f77efa0", AC.on_cron("0 0 * * *"), one_parent, False),
        ("612d7d015db28b363dc0ea38a8d7d21c", AC.on_cron("0 * * * *"), one_parent_daily, False),
        ("4982541e273f0d5e00c500d559ce78a0", AC.on_cron("0 * * * *"), two_parents, False),
        ("563b2dae9572bc93d01b847a5b9e920d", AC.on_cron("0 * * * *"), two_parents_daily, False),
        # same as above
        ("0a35066676dfc02f1afc906a671860ac", AC.eager(), one_parent, False),
        ("b10e8c43ac5c619a3f9515f402e3f3f3", AC.eager(), one_parent, True),
        ("183dbebeea08971f12f5c9e1220b87a0", AC.eager(), one_parent_daily, False),
        (
            # note: identical hash to the above
            "8c05e2d37a7ed8b7705fba907ce5d433",
            AC.eager().allow(AssetSelection.all()),
            one_parent_daily,
            False,
        ),
        ("4d0cfd5ae88cd83c00ff23ead3228923", AC.eager(), two_parents, False),
        ("69972fd8dc81a14c13125330afa4c9e1", AC.eager(), two_parents_daily, False),
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
        state = state.with_current_time("2024-01-01T01:01").with_runs(run_request("A"))

    state, result = await state.with_current_time("2024-01-01T01:02").evaluate("downstream")
    assert result.value_hash == expected_value_hash


@pytest.mark.parametrize(
    "sequence",
    [
        ["initial", "updated", "updated", "updated", "updated"],
        ["initial", "updated", "initial", "updated", "initial"],
        ["initial", "initial", "initial", "initial", "updated"],
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
    assert condition.get_node_unique_id(
        parent_unique_id=None, index=None, target_key=None
    ) == non_secure_md5_hash_str(f"{None}{None}{condition.name}".encode())
    assert condition.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=None, target_key=None
    ) == [non_secure_md5_hash_str(f"{None}{None}{condition.base_name}".encode())]


@pytest.mark.parametrize(
    "make_cond",
    [
        pytest.param(AC.any_deps_match, id="any_deps_match"),
        pytest.param(AC.all_deps_match, id="all_deps_match"),
    ],
)
def test_dep_condition_id_collision_fix(make_cond) -> None:
    allow_a = make_cond(AC.missing()).allow(AssetSelection.keys("assetA"))
    allow_b = make_cond(AC.missing()).allow(AssetSelection.keys("assetB"))

    assert allow_a.get_node_unique_id(
        parent_unique_id=None, index=0, target_key=None
    ) != allow_b.get_node_unique_id(parent_unique_id=None, index=0, target_key=None)
    assert allow_a.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=0, target_key=None
    ) == allow_b.get_backcompat_node_unique_ids(parent_unique_id=None, index=0, target_key=None)

    ignore_a = make_cond(AC.missing()).ignore(AssetSelection.keys("assetC"))
    ignore_b = make_cond(AC.missing()).ignore(AssetSelection.keys("assetD"))

    assert ignore_a.get_node_unique_id(
        parent_unique_id=None, index=0, target_key=None
    ) != ignore_b.get_node_unique_id(parent_unique_id=None, index=0, target_key=None)
    assert ignore_a.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=0, target_key=None
    ) == ignore_b.get_backcompat_node_unique_ids(
        parent_unique_id=None, index=0, target_key=None
    )


def test_labeled_condition_node_unique_id_backcompat() -> None:
    condition = AC.missing().with_label("my_label")

    assert condition.get_node_unique_id(
        parent_unique_id="parent", index=0, target_key=None
    ) == non_secure_md5_hash_str(f"parent0{condition.name}{condition.get_label()}".encode())
    assert condition.get_backcompat_node_unique_ids(
        parent_unique_id="parent", index=0, target_key=None
    ) == [non_secure_md5_hash_str(f"parent0{condition.name}".encode())]


def test_since_condition_cursor_backcompat() -> None:
    cond_a = AC.any_deps_match(AC.missing()).allow(AssetSelection.keys("assetA")).since_last_handled()
    cond_b = AC.any_deps_match(AC.missing()).allow(AssetSelection.keys("assetB")).since_last_handled()

    assert cond_a.get_node_unique_id(
        parent_unique_id="parent", index=0, target_key=None
    ) != cond_b.get_node_unique_id(parent_unique_id="parent", index=0, target_key=None)
    assert cond_a.get_backcompat_node_unique_ids(
        parent_unique_id="parent", index=0, target_key=None
    ) == cond_b.get_backcompat_node_unique_ids(
        parent_unique_id="parent", index=0, target_key=None
    )


def test_newly_true_condition_cursor_backcompat() -> None:
    cond_a = AC.any_deps_match(AC.missing()).allow(AssetSelection.keys("assetA")).newly_true()
    cond_b = AC.any_deps_match(AC.missing()).allow(AssetSelection.keys("assetB")).newly_true()

    assert cond_a.get_node_unique_id(
        parent_unique_id="parent", index=0, target_key=None
    ) != cond_b.get_node_unique_id(parent_unique_id="parent", index=0, target_key=None)
    assert cond_a.get_backcompat_node_unique_ids(
        parent_unique_id="parent", index=0, target_key=None
    ) == cond_b.get_backcompat_node_unique_ids(
        parent_unique_id="parent", index=0, target_key=None
    )
