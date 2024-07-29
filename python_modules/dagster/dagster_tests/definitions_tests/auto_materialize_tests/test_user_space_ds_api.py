import logging
import time
from typing import AbstractSet, Iterator, NamedTuple, Sequence

import pytest
from dagster import AutomationCondition, asset
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.test_utils import MockedRunLauncher, in_process_test_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._daemon.sensor import execute_sensor_iteration
from dagster._serdes.serdes import deserialize_value, serialize_value
from dagster._utils import file_relative_path

from .user_space_ds_defs import downstream, upstream


class AutomationTickResult(NamedTuple):
    results: Sequence[AutomationResult]
    asset_partition_keys: AbstractSet[AssetKeyPartitionKey]


def execute_ds_ticks(defs: Definitions, n: int) -> Iterator[AutomationTickResult]:
    asset_graph = defs.get_asset_graph()

    cursor = AssetDaemonCursor.empty()
    for i in range(n):
        asset_graph_view = AssetGraphView.for_test(defs)
        data_time_resolver = CachingDataTimeResolver(
            asset_graph_view.get_inner_queryer_for_back_compat()
        )
        evaluator = AutomationConditionEvaluator(
            asset_graph=asset_graph,
            asset_keys=asset_graph.all_asset_keys,
            asset_graph_view=asset_graph_view,
            logger=logging.getLogger(__name__),
            data_time_resolver=data_time_resolver,
            cursor=cursor,
            respect_materialization_data_versions=False,
            auto_materialize_run_tags={},
            request_backfills=False,
        )
        results, to_request = evaluator.evaluate()

        cursor = cursor.with_updates(
            evaluation_id=i,
            evaluation_timestamp=time.time(),
            newly_observe_requested_asset_keys=[],
            condition_cursors=[result.get_new_cursor() for result in results],
        )

        serialized_cursor = serialize_value(cursor)
        cursor = deserialize_value(serialized_cursor, AssetDaemonCursor)

        yield AutomationTickResult(results=results, asset_partition_keys=to_request)


def execute_ds_tick(defs: Definitions) -> AutomationTickResult:
    return next(execute_ds_ticks(defs, n=1))


def test_basic_asset_scheduling_test() -> None:
    eager_policy = AutomationCondition.eager().as_auto_materialize_policy()

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
    assert result.results[0].true_subset.bool_value
    assert result.results[1].true_subset.bool_value


@pytest.fixture
def workspace():
    with instance_for_test(
        {
            "auto_materialize": {"use_sensors": True},
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"},
        }
    ) as instance:
        with in_process_test_workspace(
            instance,
            LoadableTargetOrigin(python_file=file_relative_path(__file__, "user_space_ds_defs.py")),
        ) as request_ctx:
            yield request_ctx.process_context


def test_user_space_eval(workspace: WorkspaceProcessContext) -> None:
    assert isinstance(workspace.instance.run_launcher, MockedRunLauncher)

    list(execute_sensor_iteration(workspace, logging.Logger("test"), None, None))

    launched_runs = workspace.instance.run_launcher.queue()
    assert len(launched_runs) == 1
    asset_selection = launched_runs[0].asset_selection
    assert upstream.key in asset_selection
    assert downstream.key in asset_selection
