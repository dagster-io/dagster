from typing import Optional, Sequence

import dagster._check as check
import pytest
from dagster import AutomationCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.definitions_tests.auto_materialize_tests.scenario_state import ScenarioSpec

from ..base_scenario import run_request
from ..scenario_specs import one_asset_depends_on_two, two_partitions_def
from .automation_condition_scenario import AutomationConditionScenarioState


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(AutomationCondition):
        @property
        def label(self) -> Optional[str]:
            return None

        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: AutomationContext) -> AutomationResult:
            true_candidates = {
                candidate
                for candidate in context.candidate_slice.convert_to_valid_asset_subset().asset_partitions
                if candidate in true_set
            }
            partitions_def = context.asset_graph_view.asset_graph.get(
                context.asset_key
            ).partitions_def
            return AutomationResult(
                context,
                true_slice=check.not_none(
                    context.asset_graph_view.get_asset_slice_from_subset(
                        AssetSubset.from_asset_partitions_set(
                            context.asset_key, partitions_def, true_candidates
                        )
                    )
                ),
            )

    return HardcodedCondition(), true_set


@pytest.mark.parametrize("is_any", [True, False])
def test_dep_missing_unpartitioned(is_any: bool) -> None:
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
    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    # one parent true, still one false
    true_set.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 1
    else:
        assert result.true_subset.size == 0

    # both parents true
    true_set.add(AssetKeyPartitionKey(AssetKey("B")))
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1


@pytest.mark.parametrize("is_any", [True, False])
def test_dep_missing_partitioned(is_any: bool) -> None:
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
    state, result = state.evaluate("C")
    assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(AssetKey("A"), "1"))
    state, result = state.evaluate("C")
    if is_any:
        # one parent is true for partition 1
        assert result.true_subset.size == 1
    else:
        # neither 1 nor 2 have all parents true
        assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(AssetKey("A"), "2"))
    state, result = state.evaluate("C")
    if is_any:
        # both partitions 1 and 2 have at least one true parent
        assert result.true_subset.size == 2
    else:
        # neither 1 nor 2 have all parents true
        assert result.true_subset.size == 0

    true_set.add(AssetKeyPartitionKey(AssetKey("B"), "1"))
    state, result = state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 2
    else:
        # now partition 1 has all parents true
        assert result.true_subset.size == 1

    true_set.add(AssetKeyPartitionKey(AssetKey("B"), "2"))
    state, result = state.evaluate("C")
    if is_any:
        assert result.true_subset.size == 2
    else:
        # now partition 2 has all parents true
        assert result.true_subset.size == 2


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
def test_dep_missing_partitioned_selections(
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
    state, result = state.evaluate("C")
    assert result.true_subset.size == expected_initial_result_size
    state = state.with_runs(*(run_request(s[0], s[1]) for s in materialized_asset_partitions))
    state, result = state.evaluate("C")
    assert result.true_subset.size == expected_final_result_size


complex_scenario_spec = ScenarioSpec(
    asset_specs=[
        AssetSpec("A", group_name="foo"),
        AssetSpec("B", group_name="foo"),
        AssetSpec("C", group_name="foo"),
        AssetSpec("D", group_name="bar"),
        AssetSpec("E", group_name="bar"),
        AssetSpec("downstream", deps=["A", "B", "C", "D", "E"]),
    ]
)


def test_dep_missing_complex_include() -> None:
    # true if any dependencies within the "bar" group are missing, or "A" is missing
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing(),
    ).allow(AssetSelection.keys("A") | AssetSelection.groups("bar"))
    state = AutomationConditionScenarioState(complex_scenario_spec, automation_condition=condition)

    # all start off as missing
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 1

    # A materialized, D and E still missing
    state = state.with_runs(run_request(["A"]))
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 1

    # D and E materialized, and all the other missing things are in the exclude selection
    state = state.with_runs(run_request(["D", "E"]))
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 0


def test_dep_missing_complex_exclude() -> None:
    # true if any dependencies are missing, ignoring A and anything in the "bar" group
    condition = AutomationCondition.any_deps_match(
        AutomationCondition.missing(),
    ).ignore(AssetSelection.keys("A") | AssetSelection.groups("bar"))
    state = AutomationConditionScenarioState(complex_scenario_spec, automation_condition=condition)

    # all start off as missing
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 1

    # B materialized, C still missing
    state = state.with_runs(run_request(["B"]))
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 1

    # C materialized, and all the other missing things are in the exclude selection
    state = state.with_runs(run_request(["C"]))
    state, result = state.evaluate("downstream")
    assert result.true_subset.size == 0
