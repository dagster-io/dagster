import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.asset_condition import (
    AssetCondition,
    AssetConditionResult,
)
from dagster._core.definitions.declarative_scheduling.scheduling_context import (
    SchedulingContext,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

from ..scenario_specs import one_asset_depends_on_two, two_partitions_def
from .asset_condition_scenario import AssetConditionScenarioState


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(AssetCondition):
        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: SchedulingContext) -> AssetConditionResult:
            true_candidates = {
                candidate
                for candidate in context.candidate_subset.asset_partitions
                if candidate in true_set
            }
            partitions_def = context.asset_graph_view.asset_graph.get(
                context.asset_key
            ).partitions_def
            return AssetConditionResult.create(
                context,
                true_subset=AssetSubset.from_asset_partitions_set(
                    context.asset_key, partitions_def, true_candidates
                ),
            )

    return HardcodedCondition(), true_set


@pytest.mark.parametrize("is_any", [True, False])
def test_dep_missing_unpartitioned(is_any: bool) -> None:
    inner_condition, true_set = get_hardcoded_condition()
    condition = (
        AssetCondition.any_deps_match(inner_condition)
        if is_any
        else AssetCondition.all_deps_match(inner_condition)
    )
    state = AssetConditionScenarioState(one_asset_depends_on_two, asset_condition=condition)

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
        AssetCondition.any_deps_match(inner_condition)
        if is_any
        else AssetCondition.all_deps_match(inner_condition)
    )
    state = AssetConditionScenarioState(
        one_asset_depends_on_two, asset_condition=condition
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
