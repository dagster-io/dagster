from dagster import check
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.serdes import serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info
from graphql.execution.base import ResolveInfo
from rx import Observable

from ..external import ExternalPipeline, ensure_valid_config, get_external_pipeline_or_raise
from ..fetch_runs import is_config_valid
from ..pipeline_run_storage import PipelineRunObservableSubscribe
from ..utils import ExecutionParams, UserFacingGraphQLError, capture_error
from .backfill import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    resume_partition_backfill,
)
from .launch_execution import launch_pipeline_execution, launch_pipeline_reexecution


def _force_mark_as_canceled(graphene_info, run_id):
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.roots.mutation import GrapheneTerminateRunSuccess

    instance = graphene_info.context.instance

    reloaded_run = instance.get_run_by_id(run_id)

    if not reloaded_run.is_finished:
        message = (
            "This pipeline was forcibly marked as canceled from outside the execution context. The "
            "computational resources created by the run may not have been fully cleaned up."
        )
        instance.report_run_canceled(reloaded_run, message=message)
        reloaded_run = instance.get_run_by_id(run_id)

    return GrapheneTerminateRunSuccess(GrapheneRun(reloaded_run))


@capture_error
def terminate_pipeline_execution(graphene_info, run_id, terminate_policy):
    from ...schema.errors import GrapheneRunNotFoundError
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.roots.mutation import (
        GrapheneTerminateRunFailure,
        GrapheneTerminateRunSuccess,
        GrapheneTerminateRunPolicy,
    )

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)

    force_mark_as_canceled = (
        terminate_policy == GrapheneTerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY
    )

    if not run:
        return GrapheneRunNotFoundError(run_id)

    pipeline_run = GrapheneRun(run)

    valid_status = not run.is_finished and (
        force_mark_as_canceled
        or (run.status == PipelineRunStatus.STARTED or run.status == PipelineRunStatus.QUEUED)
    )

    if not valid_status:
        return GrapheneTerminateRunFailure(
            run=pipeline_run,
            message="Run {run_id} could not be terminated due to having status {status}.".format(
                run_id=run.run_id, status=run.status.value
            ),
        )

    if (
        graphene_info.context.instance.run_coordinator
        and graphene_info.context.instance.run_coordinator.can_cancel_run(run_id)
        and graphene_info.context.instance.run_coordinator.cancel_run(run_id)
    ):

        return (
            _force_mark_as_canceled(graphene_info, run_id)
            if force_mark_as_canceled
            else GrapheneTerminateRunSuccess(pipeline_run)
        )

    return (
        _force_mark_as_canceled(graphene_info, run_id)
        if force_mark_as_canceled
        else GrapheneTerminateRunFailure(
            run=pipeline_run, message="Unable to terminate run {run_id}".format(run_id=run.run_id)
        )
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
    run = instance.get_run_by_id(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                GraphenePipelineRunLogsSubscriptionFailure(
                    missingRunId=run_id, message="Could not load run with id {}".format(run_id)
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    def _handle_events(payload):
        events, loading_past = payload
        return GraphenePipelineRunLogsSubscriptionSuccess(
            run=GrapheneRun(run),
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
