import sys

from graphql.execution.base import ResolveInfo
from rx import Observable

import dagster._check as check
from dagster.core.events import DagsterEventType, EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster.serdes import serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from ..external import ExternalPipeline, ensure_valid_config, get_external_pipeline_or_raise
from ..fetch_runs import is_config_valid
from ..pipeline_run_storage import PipelineRunObservableSubscribe
from ..utils import ExecutionParams, UserFacingGraphQLError, capture_error
from .backfill import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    resume_partition_backfill,
)
from .launch_execution import (
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    launch_reexecution_from_parent_run,
)


def _force_mark_as_canceled(instance, run_id):
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.roots.mutation import GrapheneTerminateRunSuccess

    reloaded_record = instance.get_run_records(RunsFilter(run_ids=[run_id]))[0]

    if not reloaded_record.pipeline_run.is_finished:
        message = (
            "This pipeline was forcibly marked as canceled from outside the execution context. The "
            "computational resources created by the run may not have been fully cleaned up."
        )
        instance.report_run_canceled(reloaded_record.pipeline_run, message=message)
        reloaded_record = instance.get_run_records(RunsFilter(run_ids=[run_id]))[0]

    return GrapheneTerminateRunSuccess(GrapheneRun(reloaded_record))


@capture_error
def terminate_pipeline_execution(instance, run_id, terminate_policy):
    from ...schema.errors import GrapheneRunNotFoundError
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.roots.mutation import (
        GrapheneTerminateRunFailure,
        GrapheneTerminateRunPolicy,
        GrapheneTerminateRunSuccess,
    )

    check.inst_param(instance, "instance", DagsterInstance)
    check.str_param(run_id, "run_id")

    records = instance.get_run_records(RunsFilter(run_ids=[run_id]))

    force_mark_as_canceled = (
        terminate_policy == GrapheneTerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY
    )

    if not records:
        return GrapheneRunNotFoundError(run_id)

    record = records[0]
    run = record.pipeline_run
    graphene_run = GrapheneRun(record)

    can_cancel_run = (
        run.status == PipelineRunStatus.STARTED or run.status == PipelineRunStatus.QUEUED
    )

    valid_status = not run.is_finished and (force_mark_as_canceled or can_cancel_run)

    if not valid_status:
        return GrapheneTerminateRunFailure(
            run=graphene_run,
            message="Run {run_id} could not be terminated due to having status {status}.".format(
                run_id=run.run_id, status=run.status.value
            ),
        )

    if force_mark_as_canceled:
        try:
            if instance.run_coordinator and can_cancel_run:
                instance.run_coordinator.cancel_run(run_id)
        except:
            instance.report_engine_event(
                "Exception while attempting to force-terminate run. Run will still be marked as canceled.",
                pipeline_name=run.pipeline_name,
                run_id=run.run_id,
                engine_event_data=EngineEventData(
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                ),
            )
        return _force_mark_as_canceled(instance, run_id)

    if instance.run_coordinator and can_cancel_run and instance.run_coordinator.cancel_run(run_id):
        return GrapheneTerminateRunSuccess(graphene_run)

    return GrapheneTerminateRunFailure(
        run=graphene_run, message="Unable to terminate run {run_id}".format(run_id=run.run_id)
    )


@capture_error
def delete_pipeline_run(graphene_info, run_id):
    from ...schema.errors import GrapheneRunNotFoundError
    from ...schema.roots.mutation import GrapheneDeletePipelineRunSuccess

    instance = graphene_info.context.instance

    if not instance.has_run(run_id):
        return GrapheneRunNotFoundError(run_id)

    instance.delete_run(run_id)

    return GrapheneDeletePipelineRunSuccess(run_id)


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.pipelines.subscription import (
        GraphenePipelineRunLogsSubscriptionFailure,
        GraphenePipelineRunLogsSubscriptionSuccess,
    )
    from ..events import from_event_record

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")
    check.opt_int_param(after, "after")
    instance = graphene_info.context.instance
    records = instance.get_run_records(RunsFilter(run_ids=[run_id]))

    if not records:

        def _get_error_observable(observer):
            observer.on_next(
                GraphenePipelineRunLogsSubscriptionFailure(
                    missingRunId=run_id, message="Could not load run with id {}".format(run_id)
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    record = records[0]
    run = record.pipeline_run

    def _handle_events(payload):
        events, loading_past = payload
        return GraphenePipelineRunLogsSubscriptionSuccess(
            run=GrapheneRun(record),
            messages=[from_event_record(event, run.pipeline_name) for event in events],
            hasMorePastEvents=loading_past,
        )

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(_handle_events)


def get_compute_log_observable(graphene_info, run_id, step_key, io_type, cursor=None):
    from ...schema.logs.compute_logs import from_compute_log_file

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")
    check.str_param(step_key, "step_key")
    check.inst_param(io_type, "io_type", ComputeIOType)
    check.opt_str_param(cursor, "cursor")

    return graphene_info.context.instance.compute_log_manager.observable(
        run_id, step_key, io_type, cursor
    ).map(lambda update: from_compute_log_file(graphene_info, update))


@capture_error
def wipe_assets(graphene_info, asset_keys):
    from ...schema.roots.mutation import GrapheneAssetWipeSuccess

    instance = graphene_info.context.instance
    instance.wipe_assets(asset_keys)
    return GrapheneAssetWipeSuccess(assetKeys=asset_keys)
