import logging
from typing import AbstractSet, NamedTuple, Sequence

import mock
import pytest
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
from dagster._core.test_utils import MockedRunLauncher, in_process_test_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._daemon.asset_daemon import AssetDaemon
from dagster._utils import file_relative_path

from .user_space_ds_defs import amp_sensor, defs, downstream, upstream


class SchedulingTickResult(NamedTuple):
    evaluation_states: Sequence[AssetConditionEvaluationState]
    asset_partition_keys: AbstractSet[AssetKeyPartitionKey]


def execute_ds_tick(defs: Definitions) -> SchedulingTickResult:
    asset_graph = defs.get_asset_graph()
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
        cursor=AssetDaemonCursor.empty(),
        respect_materialization_data_versions=True,
        auto_materialize_run_tags={},
    )
    result = evaluator.evaluate()

    return SchedulingTickResult(
        evaluation_states=result[0],
        asset_partition_keys=result[1],
    )


def test_basic_asset_scheduling_test() -> None:
    result = execute_ds_tick(defs)
    assert result
    assert result.asset_partition_keys == {
        AssetKeyPartitionKey(upstream.key),
        AssetKeyPartitionKey(downstream.key),
    }
    # both are true because both missing
    assert result.evaluation_states[0].true_subset.bool_value
    assert result.evaluation_states[1].true_subset.bool_value


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
    with mock.patch(
        "user_space_ds_defs.amp_sensor._evaluation_fn",
        wraps=amp_sensor._evaluation_fn,  # noqa
    ) as mocked_eval:
        asset_daemon = AssetDaemon(
            settings=workspace.instance.get_auto_materialize_settings(),
            pre_sensor_interval_seconds=42,
        )

        list(
            asset_daemon._run_iteration_impl(  # noqa: SLF001
                workspace,
                threadpool_executor=None,
                amp_tick_futures={},
                debug_crash_flags={},
            )
        )

        assert isinstance(workspace.instance.run_launcher, MockedRunLauncher)
        launched_runs = workspace.instance.run_launcher.queue()
        assert len(launched_runs) == 1
        asset_selection = launched_runs[0].asset_selection
        assert upstream.key in asset_selection
        assert downstream.key in asset_selection
        mocked_eval.assert_called()
