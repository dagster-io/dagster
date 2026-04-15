from collections.abc import Sequence

import dagster as dg
import pytest
from dagster import AutomationCondition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import run_request
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset_depends_on_two,
    two_partitions_def,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_state import ScenarioSpec


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(dg.AutomationCondition):
        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: AutomationContext) -> dg.AutomationResult:
            filtered_true_set = {akpk for akpk in true_set if akpk.asset_key == context.key}
            if context.partitions_def:
                true_subset = context.candidate_subset.compute_intersection_with_partition_keys(
                    {apk.partition_key for apk in filtered_true_set}
                )
            else:
                true_subset = (
                    context.asset_graph_view.get_full_subset(key=context.key)
                    if filtered_true_set
                    else context.asset_graph_view.get_empty_subset(key=context.key)
                )
            return dg.AutomationResult(context, true_subset=true_subset)

    return HardcodedCondition(), true_set


@pytest.mark.asyncio
@pytest.mark.parametrize("is_any", [True, False])
async def test_dep_missing_unpartitioned(is_any: bool) -> None:
    inner_condition, true_set = get_hardcoded_condition()
    condition = (
        AutomationCondition.any_deps_match(inner_condition)
        if is_any
        else AutomationCondition.all_deps_match(inner_condition)
    )
    state = AutomationConditionScenarioState(
        one_asset_depends_on_two, automation_condition=condition
    )

    # neither parent is true
    state, result = await state.evaluate("C")
    assert result.true_subset.size == 0

    # one parent true, still one false
    true_set.add(AssetKeyPartitionKey(dg.AssetKey("A")))
    state, result = await state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 1
    else:
        assert result.true_subset.size == 0

    # both parents true
    true_set.add(AssetKeyPartitionKey(dg.AssetKey("B")))
    state, result = await state.evaluate("C")
    assert result.true_subset.size == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("is_any", [True, False])
async def test_dep_missing_partitioned(is_any: bool) -> None:
    inner_condition, true_set = get_hardcoded_condition()
    condition = (
        AutomationCondition.any_deps_match(inner_condition)
        if is_any
        else AutomationCondition.all_deps_match(inner_condition)
    )
    state = AutomationConditionScenarioState(
        one_asset_depends_on_two, automation_condition=condition
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no parents true
    state, result = await state.evaluate("C")
    assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(dg.AssetKey("A"), "1"))
    state, result = await state.evaluate("C")
    if is_any:
        # one parent is true for partition 1
        assert result.true_subset.size == 1
    else:
        # neither 1 nor 2 have all parents true
        assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(dg.AssetKey("A"), "2"))
    state, result = await state.evaluate("C")
    if is_any:
        # both partitions 1 and 2 have at least one true parent
        assert result.true_subset.size == 2
    else:
        # neither 1 nor 2 have all parents true
        assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(dg.AssetKey("B"), "1"))
    state, result = await state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 2
    else:
        # now partition 1 has all parents true
        assert result.true_subset.size == 1

    true_set.add(AssetKeyPartitionKey(dg.AssetKey("B"), "2"))
    state, result = await state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 2
    else:
        # now partition 2 has all parents true
        assert result.true_subset.size == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("is_any", [True, False])
@pytest.mark.parametrize("is_include", [True, False])
@pytest.mark.parametrize(
    "expected_initial_result_size,materialized_asset_partitions,expected_final_result_size",
    [
        # after A is materialized, B is still missing, but is ignored
        (2, ["A1"], 1),
        (2, ["A1", "A2"], 0),
        # materializations of B have no effect
        (2, ["A1", "B2"], 1),
        (2, ["B1", "B2"], 2),
    ],
)
async def test_dep_missing_partitioned_selections(
    is_any: bool,
    is_include: bool,
    expected_initial_result_size: int,
    materialized_asset_partitions: Sequence[str],
    expected_final_result_size: int,
) -> None:
    # NOTE: because all selections resolve to a single parent asset, ANY and ALL return the same
    # results
    if is_any:
        condition = AutomationCondition.any_deps_match(AutomationCondition.missing())
    else:
        condition = AutomationCondition.all_deps_match(AutomationCondition.missing())

    if is_include:
        condition = condition.allow(AssetSelection.keys("A"))
    else:
        condition = condition.ignore(AssetSelection.keys("B"))

    state = AutomationConditionScenarioState(
        one_asset_depends_on_two, automation_condition=condition
    ).with_asset_properties(partitions_def=two_partitions_def)
    # all parents are missing
    state, result = await state.evaluate("C")
    assert result.true_subset.size == expected_initial_result_size
    state = state.with_runs(*(run_request(s[0], s[1]) for s in materialized_asset_partitions))
    state, result = await state.evaluate("C")
    assert result.true_subset.size == expected_final_result_size


complex_scenario_spec = ScenarioSpec(
    asset_specs=[
        dg.AssetSpec("A", group_name="foo"),
        dg.AssetSpec("B", group_name="foo"),
        dg.AssetSpec("C", group_name="foo"),
        dg.AssetSpec("D", group_name="bar"),
        dg.AssetSpec("E", group_name="bar"),
        dg.AssetSpec("downstream", deps=["A", "B", "C", "D", "E"]),
    ]
)


@pytest.mark.asyncio
async def test_dep_missing_complex_include() -> None:
    # true if any dependencies within the "bar" group are missing, or "A" is missing
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing(),
    ).allow(AssetSelection.keys("A") | AssetSelection.groups("bar"))
    state = AutomationConditionScenarioState(complex_scenario_spec, automation_condition=condition)

    # all start off as missing
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 1

    # A materialized, D and E still missing
    state = state.with_runs(run_request(["A"]))
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 1

    # D and E materialized, and all the other missing things are in the exclude selection
    state = state.with_runs(run_request(["D", "E"]))
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 0


@pytest.mark.asyncio
async def test_dep_missing_complex_exclude() -> None:
    # true if any dependencies are missing, ignoring A and anything in the "bar" group
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing(),
    ).ignore(AssetSelection.keys("A") | AssetSelection.groups("bar"))
    state = AutomationConditionScenarioState(complex_scenario_spec, automation_condition=condition)

    # all start off as missing
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 1

    # B materialized, C still missing
    state = state.with_runs(run_request(["B"]))
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 1

    # C materialized, and all the other missing things are in the exclude selection
    state = state.with_runs(run_request(["C"]))
    state, result = await state.evaluate("downstream")
    assert result.true_subset.size == 0


def _make_linear_four_assets(
    condition: AutomationCondition,
    views: Sequence[str] = (),
) -> list[dg.AssetsDefinition]:
    """A -> B -> C -> D, with the condition applied to D.

    Assets named in ``views`` are marked as ``is_virtual=True``.
    """

    @dg.asset(is_virtual="A" in views)
    def A() -> None: ...

    @dg.asset(deps=["A"], is_virtual="B" in views)
    def B() -> None: ...

    @dg.asset(deps=["B"], is_virtual="C" in views)
    def C() -> None: ...

    @dg.asset(deps=["C"], automation_condition=condition)
    def D() -> None: ...

    return [A, B, C, D]


def test_resolve_through_virtual_basic() -> None:
    """D's direct dep is C (a view). Looking through it, effective dep becomes B."""
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing()
    ).resolve_through_virtual()
    assets = _make_linear_four_assets(condition, views=["C"])
    instance = dg.DagsterInstance.ephemeral()

    # B is missing — effective dep after looking through view C — so D matches
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 1

    # Materialize B — now the effective dep is no longer missing
    instance.report_runless_asset_event(dg.AssetMaterialization("B"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_resolve_through_virtual_recursive() -> None:
    """Looking through views B and C from D should find A as the effective dep."""
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing()
    ).resolve_through_virtual()
    assets = _make_linear_four_assets(condition, views=["B", "C"])
    instance = dg.DagsterInstance.ephemeral()

    # A is missing — effective dep after looking through views B and C
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 1

    # Materialize A — now no effective deps are missing
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_resolve_through_virtual_with_allow() -> None:
    """resolve_through_virtual applied first, then allow filters the expanded set."""
    condition = (
        AutomationCondition.any_deps_match(AutomationCondition.missing())
        .resolve_through_virtual()
        .allow(AssetSelection.keys("A"))
    )
    # C is a view, so D's effective dep becomes B — but allow only permits A
    assets = _make_linear_four_assets(condition, views=["C"])
    instance = dg.DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 0


def test_resolve_through_virtual_with_ignore() -> None:
    """resolve_through_virtual applied first, then ignore filters the expanded set."""
    condition = (
        AutomationCondition.any_deps_match(AutomationCondition.missing())
        .resolve_through_virtual()
        .ignore(AssetSelection.keys("B"))
    )
    # C is a view, so D's effective dep becomes B — but B is ignored
    assets = _make_linear_four_assets(condition, views=["C"])
    instance = dg.DagsterInstance.ephemeral()

    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 0


def test_resolve_through_virtual_all_deps() -> None:
    """all_deps_match works with resolve_through_virtual."""
    condition = AutomationCondition.all_deps_match(
        AutomationCondition.missing()
    ).resolve_through_virtual()
    # B and C are views, so D's only effective dep is A
    assets = _make_linear_four_assets(condition, views=["B", "C"])
    instance = dg.DagsterInstance.ephemeral()

    # A is missing — the only effective dep, so all_deps_match(missing) is satisfied
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 1

    # Materialize A — now no effective deps are missing
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_resolve_through_virtual_no_views() -> None:
    """No assets are views — behavior unchanged from without resolve_through_virtual."""
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing()
    ).resolve_through_virtual()
    assets = _make_linear_four_assets(condition, views=[])
    instance = dg.DagsterInstance.ephemeral()

    # D's direct dep is C (not a view), C is missing
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 1

    # Materialize C — direct dep no longer missing
    instance.report_runless_asset_event(dg.AssetMaterialization("C"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_on_cron_resolve_through_virtual() -> None:
    r"""on_cron().resolve_through_virtual() propagates through the AndAutomationCondition
    down to the dep conditions.

    Graph:
        NV1   NV2   E1   E2
         |     |     \\  /
         |    V1      V3   (view, chain)
          \\   |      |
           \\  |     V2    (view, chain)
            \\ |    /
            target

    target has 3 direct deps: NV1 (non-view), V1 (view -> NV2), V2 (view -> V3 (view) -> E1, E2).
    With resolve_through_virtual, effective deps are: NV1, NV2, E1, E2.
    """
    import datetime

    @dg.asset
    def NV1() -> None: ...

    @dg.asset
    def NV2() -> None: ...

    @dg.asset
    def E1() -> None: ...

    @dg.asset
    def E2() -> None: ...

    @dg.asset(deps=["E1", "E2"], is_virtual=True)
    def V3() -> None: ...

    @dg.asset(deps=["V3"], is_virtual=True)
    def V2() -> None: ...

    @dg.asset(deps=["NV2"], is_virtual=True)
    def V1() -> None: ...

    @dg.asset(
        deps=["NV1", "V1", "V2"],
        automation_condition=AutomationCondition.on_cron("0 * * * *").resolve_through_virtual(),
    )
    def target() -> None: ...

    assets = [NV1, NV2, E1, E2, V3, V2, V1, target]
    instance = dg.DagsterInstance.ephemeral()
    current_time = datetime.datetime(2020, 2, 2, 0, 55)

    # baseline — no cron tick yet
    result = dg.evaluate_automation_conditions(
        defs=assets, instance=instance, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # cross cron boundary — deps not updated yet
    current_time += datetime.timedelta(minutes=10)
    result = dg.evaluate_automation_conditions(
        defs=assets, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0

    # materialize some but not all effective deps — still not ready
    instance.report_runless_asset_event(dg.AssetMaterialization("NV1"))
    instance.report_runless_asset_event(dg.AssetMaterialization("NV2"))
    instance.report_runless_asset_event(dg.AssetMaterialization("E1"))
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=assets, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 0  # E2 still hasn't been updated

    # materialize E2 — now all effective deps are updated
    instance.report_runless_asset_event(dg.AssetMaterialization("E2"))
    current_time += datetime.timedelta(minutes=1)
    result = dg.evaluate_automation_conditions(
        defs=assets, instance=instance, cursor=result.cursor, evaluation_time=current_time
    )
    assert result.total_requested == 1


def test_eager_resolve_through_virtual() -> None:
    r"""eager().resolve_through_virtual() propagates through the AndAutomationCondition
    down to all dep conditions (any_deps_updated, any_deps_missing, any_deps_in_progress).

    Same graph as test_on_cron_resolve_through_virtual:
        NV1   NV2   E1   E2
         |     |     \\  /
         |    V1      V3   (view, chain)
          \\   |      |
           \\  |     V2    (view, chain)
            \\ |    /
            target

    Effective deps with resolve_through_virtual: NV1, NV2, E1, E2.
    """

    @dg.asset
    def NV1() -> None: ...

    @dg.asset
    def NV2() -> None: ...

    @dg.asset
    def E1() -> None: ...

    @dg.asset
    def E2() -> None: ...

    @dg.asset(deps=["E1", "E2"], is_virtual=True)
    def V3() -> None: ...

    @dg.asset(deps=["V3"], is_virtual=True)
    def V2() -> None: ...

    @dg.asset(deps=["NV2"], is_virtual=True)
    def V1() -> None: ...

    @dg.asset(
        deps=["NV1", "V1", "V2"],
        automation_condition=AutomationCondition.eager().resolve_through_virtual(),
    )
    def target() -> None: ...

    assets = [NV1, NV2, E1, E2, V3, V2, V1, target]
    instance = dg.DagsterInstance.ephemeral()

    # baseline — all effective deps are missing, so any_deps_missing blocks
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance)
    assert result.total_requested == 0

    # materialize some effective deps — still blocked by missing E2
    instance.report_runless_asset_event(dg.AssetMaterialization("NV1"))
    instance.report_runless_asset_event(dg.AssetMaterialization("NV2"))
    instance.report_runless_asset_event(dg.AssetMaterialization("E1"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # materialize E2 — all effective deps present, target is newly_missing so eager fires
    instance.report_runless_asset_event(dg.AssetMaterialization("E2"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # handle the request, then update one effective dep — should fire again
    instance.report_runless_asset_event(dg.AssetMaterialization("target"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    instance.report_runless_asset_event(dg.AssetMaterialization("NV1"))
    result = dg.evaluate_automation_conditions(defs=assets, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1


def test_any_dep_invalid_selection() -> None:
    @dg.asset(
        automation_condition=dg.AutomationCondition.any_deps_match(
            AutomationCondition.missing()
        ).allow(dg.AssetSelection.keys("does_not_exist"))
    )
    def my_asset() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(defs=[my_asset], instance=instance)

    assert result.total_requested == 0
