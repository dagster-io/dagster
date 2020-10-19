from __future__ import absolute_import

import sys
import time

from dagster_graphql.implementation.fetch_runs import is_config_valid
from dagster_graphql.schema.pipelines import DauphinPipeline
from dagster_graphql.schema.runs import (
    from_compute_log_file,
    from_dagster_event_record,
    from_event_record,
)
from graphql.execution.base import ResolveInfo
from rx import Observable

from dagster import check
from dagster.core.definitions import IPipeline
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import (
    DagsterInvalidConfigError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.retries import Retries
from dagster.core.host_representation import ExternalExecutionPlan
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import ExecutionConfig
from dagster.serdes import serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from ..external import (
    ExternalPipeline,
    ensure_valid_config,
    ensure_valid_step_keys,
    get_external_pipeline_or_raise,
)
from ..pipeline_run_storage import PipelineRunObservableSubscribe
from ..resume_retry import get_retry_steps_from_execution_plan
from ..utils import ExecutionParams, UserFacingGraphQLError, capture_dauphin_error
from .backfill import create_and_launch_partition_backfill
from .launch_execution import launch_pipeline_execution, launch_pipeline_reexecution
from .trigger import trigger_execution


@capture_dauphin_error
def terminate_pipeline_execution(graphene_info, run_id):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)

    if not run:
        return graphene_info.schema.type_named("PipelineRunNotFoundError")(run_id)

    dauphin_run = graphene_info.schema.type_named("PipelineRun")(run)

    if run.status != PipelineRunStatus.STARTED:
        return graphene_info.schema.type_named("TerminatePipelineExecutionFailure")(
            run=dauphin_run,
            message="Run {run_id} is not in a started state. Current status is {status}".format(
                run_id=run.run_id, status=run.status.value
            ),
        )

    can_not_term = graphene_info.schema.type_named("TerminatePipelineExecutionFailure")(
        run=dauphin_run, message="Unable to terminate run {run_id}".format(run_id=run.run_id)
    )

    if (
        graphene_info.context.instance.run_launcher
        and graphene_info.context.instance.run_launcher.can_terminate(run_id)
    ):
        if not graphene_info.context.instance.run_launcher.terminate(run_id):
            return can_not_term

        return graphene_info.schema.type_named("TerminatePipelineExecutionSuccess")(dauphin_run)

    else:
        return can_not_term


@capture_dauphin_error
def delete_pipeline_run(graphene_info, run_id):
    instance = graphene_info.context.instance

    if not instance.has_run(run_id):
        return graphene_info.schema.type_named("PipelineRunNotFoundError")(run_id)

    instance.delete_run(run_id)

    return graphene_info.schema.type_named("DeletePipelineRunSuccess")(run_id)


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")
    check.opt_int_param(after, "after")
    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named("PipelineRunLogsSubscriptionFailure")(
                    missingRunId=run_id, message="Could not load run with id {}".format(run_id)
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(
        lambda events: graphene_info.schema.type_named("PipelineRunLogsSubscriptionSuccess")(
            run=graphene_info.schema.type_named("PipelineRun")(run),
            messages=[from_event_record(event, run.pipeline_name) for event in events],
        )
    )


def get_compute_log_observable(graphene_info, run_id, step_key, io_type, cursor=None):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(run_id, "run_id")
    check.str_param(step_key, "step_key")
    check.inst_param(io_type, "io_type", ComputeIOType)
    check.opt_str_param(cursor, "cursor")

    return graphene_info.context.instance.compute_log_manager.observable(
        run_id, step_key, io_type, cursor
    ).map(lambda update: from_compute_log_file(graphene_info, update))
