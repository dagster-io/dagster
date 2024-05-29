import logging
import time
from typing import AbstractSet, Iterator, NamedTuple, Sequence

from dagster import SchedulingCondition, asset
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_scheduling.scheduling_condition_evaluator import (
    SchedulingConditionEvaluator,
)
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionEvaluationState,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKeyPartitionKey


class SchedulingTickResult(NamedTuple):
    evaluation_states: Sequence[AssetConditionEvaluationState]
    asset_partition_keys: AbstractSet[AssetKeyPartitionKey]


def execute_ds_ticks(defs: Definitions, n: int) -> Iterator[SchedulingTickResult]:
    asset_graph = defs.get_asset_graph()

    cursor = AssetDaemonCursor.empty()
    for i in range(n):
        asset_graph_view = AssetGraphView.for_test(defs)
        data_time_resolver = CachingDataTimeResolver(
            asset_graph_view.get_inner_queryer_for_back_compat()
        )
        evaluator = SchedulingConditionEvaluator(
            asset_graph=asset_graph,
            asset_keys=asset_graph.all_asset_keys,
            asset_graph_view=asset_graph_view,
            logger=logging.getLogger(__name__),
            data_time_resolver=data_time_resolver,
            cursor=cursor,
            respect_materialization_data_versions=False,
            auto_materialize_run_tags={},
        )
        result = evaluator.evaluate()

        cursor = cursor.with_updates(
            evaluation_id=i,
            evaluation_timestamp=time.time(),
            newly_observe_requested_asset_keys=[],
            evaluation_state=result[0],
        )

        yield SchedulingTickResult(evaluation_states=result[0], asset_partition_keys=result[1])


def execute_ds_tick(defs: Definitions) -> SchedulingTickResult:
    return next(execute_ds_ticks(defs, n=1))


def test_basic_asset_scheduling_test() -> None:
    eager_policy = SchedulingCondition.eager().as_auto_materialize_policy()

    @asset(auto_materialize_policy=eager_policy)
    def upstream() -> None: ...

    @asset(
        deps=[upstream],
        auto_materialize_policy=eager_policy,
    )
    def downstream() -> None: ...

    assert upstream
    assert downstream

    defs = Definitions([upstream, downstream])

    result = execute_ds_tick(defs)
    assert result
    assert result.asset_partition_keys == {
        AssetKeyPartitionKey(upstream.key),
        AssetKeyPartitionKey(downstream.key),
    }
    # both are true because both missing
    assert result.evaluation_states[0].true_subset.bool_value
    assert result.evaluation_states[1].true_subset.bool_value
