import datetime
import logging
from typing import Any, Mapping, Optional

from dagster import _check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_daemon_context import build_run_requests
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.declarative_scheduling.scheduling_condition_evaluator import (
    SchedulingConditionEvaluator,
    SchedulingConditionEvaluatorArguments,
)
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
)
from dagster._core.definitions.utils import check_valid_name, normalize_tags
from dagster._daemon.asset_daemon import (
    asset_daemon_cursor_from_instigator_serialized_cursor,
    asset_daemon_cursor_to_instigator_serialized_cursor,
)


def evaluation_fn(context: SensorEvaluationContext):
    repository_def = check.not_none(context.repository_def)

    asset_daemon_cursor = asset_daemon_cursor_from_instigator_serialized_cursor(
        serialized_cursor=context.cursor, asset_graph=repository_def.asset_graph
    )

    asset_graph_view = AssetGraphView.create(
        instance=context.instance,
        asset_graph=repository_def.asset_graph,
        effective_dt=datetime.datetime.now(),  # where should this come from
        last_event_id=None,  # volatile for now
    )

    instance_queryer = asset_graph_view.get_inner_queryer_for_back_compat()

    # should not have to get this in new API
    data_time_resolver = CachingDataTimeResolver(instance_queryer=instance_queryer)

    asset_graph = repository_def.asset_graph
    auto_run_tags = {}

    evaluator = SchedulingConditionEvaluator(
        asset_graph=asset_graph,
        asset_graph_view=asset_graph_view,
        logger=logging.getLogger(__name__),  # what is the right loggers
        data_time_resolver=data_time_resolver,
        evaluator_arguments=SchedulingConditionEvaluatorArguments(
            # TODO, asset_keys from asset selection
            asset_keys=repository_def.asset_graph.all_asset_keys,
            cursor=asset_daemon_cursor,
            respect_materialization_data_versions=True,
            auto_materialize_run_tags=auto_run_tags,
        ),
    )

    evaluation_state, to_request = evaluator.evaluate()

    # TODO, launch NotABackfill instead of runs
    run_requests = [
        *build_run_requests(
            asset_partitions=to_request,
            asset_graph=asset_graph,
            run_tags=auto_run_tags,
        ),
    ]

    new_cursor = asset_daemon_cursor.with_updates(
        # without threads is this all we need?
        evaluation_id=asset_daemon_cursor.evaluation_id + 1,
        evaluation_state=evaluation_state,
        newly_observe_requested_asset_keys=[],
        evaluation_timestamp=instance_queryer.evaluation_time.timestamp(),
    )

    cursor = asset_daemon_cursor_to_instigator_serialized_cursor(new_cursor)

    return SensorResult(run_requests=run_requests, cursor=cursor)


# TODO rename this
class DSSensorDefinition(SensorDefinition):
    def __init__(
        self,
        name: str,
        *,
        asset_selection: CoercibleToAssetSelection,
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
    ):
        self._run_tags = normalize_tags(run_tags).tags

        super(DSSensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=None,
            evaluation_fn=evaluation_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=None,
            jobs=None,
            default_status=default_status,
            required_resource_keys=None,
            asset_selection=asset_selection,
        )
