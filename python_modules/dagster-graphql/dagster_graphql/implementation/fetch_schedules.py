import glob
import os

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.utils import merge_dicts

from .utils import ExecutionMetadata, ExecutionParams, UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    repository = graphene_info.context.get_repository()
    instance = graphene_info.context.instance
    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    runningSchedules = [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in instance.all_schedules(repository)
    ]

    return graphene_info.schema.type_named('Scheduler')(runningSchedules=runningSchedules)


@capture_dauphin_error
def get_schedule_or_error(graphene_info, schedule_name):
    repository = graphene_info.context.get_repository()
    instance = graphene_info.context.instance
    schedule = instance.get_schedule_by_name(repository, schedule_name)

    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(schedule_name=schedule_name)
        )

    return graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=schedule)


def execution_params_for_schedule(graphene_info, schedule_def, pipeline_def):
    schedule_context = ScheduleExecutionContext(graphene_info.context.instance)

    # Get environment_dict
    with user_code_error_boundary(
        ScheduleExecutionError,
        lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
        '{schedule_name}'.format(schedule_name=schedule_def.name),
    ):
        environment_dict = schedule_def.get_environment_dict(schedule_context)

    # Get tags
    with user_code_error_boundary(
        ScheduleExecutionError,
        lambda: 'Error occurred during the execution of tags_fn for schedule '
        '{schedule_name}'.format(schedule_name=schedule_def.name),
    ):
        user_tags = schedule_def.get_tags(schedule_context)

    pipeline_tags = pipeline_def.tags or {}
    check.invariant('dagster/schedule_name' not in user_tags)
    tags = merge_dicts(
        pipeline_tags, merge_dicts({'dagster/schedule_name': schedule_def.name}, user_tags)
    )

    selector = schedule_def.selector
    mode = schedule_def.mode

    return ExecutionParams(
        selector=selector,
        environment_dict=environment_dict,
        mode=mode,
        execution_metadata=ExecutionMetadata(tags=tags, run_id=None),
        step_keys=None,
        previous_run_id=None,
    )


def get_scheduler_handle(graphene_info):
    scheduler_handle = graphene_info.context.scheduler_handle
    if not scheduler_handle:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    return scheduler_handle


def get_dagster_schedule_def(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    scheduler_handle = get_scheduler_handle(graphene_info)
    schedule_definition = scheduler_handle.get_schedule_def_by_name(schedule_name)
    if not schedule_definition:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleDefinitionNotFoundError')(
                schedule_name=schedule_name
            )
        )

    return schedule_definition


def get_dagster_schedule(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    repository = graphene_info.context.get_repository()
    instance = graphene_info.context.instance
    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    schedule = instance.get_schedule_by_name(repository, schedule_name)
    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(schedule_name=schedule_name)
        )

    return schedule


def get_schedule_attempt_filenames(graphene_info, schedule_name):
    instance = graphene_info.context.instance
    repository = graphene_info.context.get_repository()
    log_dir = instance.log_path_for_schedule(repository, schedule_name)
    return glob.glob(os.path.join(log_dir, "*.result"))
