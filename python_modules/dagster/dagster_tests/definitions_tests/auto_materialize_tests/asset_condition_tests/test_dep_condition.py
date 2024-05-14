from typing import Sequence

import dagster._check as check
import pytest
from dagster import AssetSelection, SchedulingCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.scheduling_condition import SchedulingResult
from dagster._core.definitions.declarative_scheduling.scheduling_context import (
    SchedulingContext,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

from ..base_scenario import run_request
from ..scenario_specs import one_asset_depends_on_two, two_partitions_def
from .asset_condition_scenario import SchedulingConditionScenarioState


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(SchedulingCondition):
        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: SchedulingContext) -> SchedulingResult:
            true_candidates = {
                candidate
                for candidate in context.candidate_slice.convert_to_valid_asset_subset().asset_partitions
                if candidate in true_set
            }
            partitions_def = context.asset_graph_view.asset_graph.get(
                context.asset_key
            ).partitions_def
            return SchedulingResult.create(
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
        SchedulingCondition.any_deps_match(inner_condition)
        if is_any
        else SchedulingCondition.all_deps_match(inner_condition)
    )
    state = SchedulingConditionScenarioState(
        one_asset_depends_on_two, scheduling_condition=condition
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
        SchedulingCondition.any_deps_match(inner_condition)
        if is_any
        else SchedulingCondition.all_deps_match(inner_condition)
    )
    state = SchedulingConditionScenarioState(
        one_asset_depends_on_two, scheduling_condition=condition
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
    expected_initial_result_size: int,
    materialized_asset_partitions: Sequence[str],
    expected_final_result_size: int,
) -> None:
    # NOTE: because all selections resolve to a single parent asset, ANY and ALL return the same
    # results
    fn = SchedulingCondition.any_deps_match if is_any else SchedulingCondition.all_deps_match
    condition = fn(
        SchedulingCondition.missing(),
        dep_selection=AssetSelection.keys("A"),
    )
    state = SchedulingConditionScenarioState(
        one_asset_depends_on_two, scheduling_condition=condition
    ).with_asset_properties(partitions_def=two_partitions_def)

    # all parents are missing
    state, result = state.evaluate("C")
    assert result.true_subset.size == expected_initial_result_size

    state = state.with_runs(*(run_request(s[0], s[1]) for s in materialized_asset_partitions))
    state, result = state.evaluate("C")
    assert result.true_subset.size == expected_final_result_size
