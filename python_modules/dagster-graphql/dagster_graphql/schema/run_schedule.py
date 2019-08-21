import json
import sys

from dagster_graphql import dauphin
from dagster_graphql.implementation.utils import UserFacingGraphQLError, capture_dauphin_error
from dagster_graphql.schema.errors import DauphinSchedulerNotDefinedError

from dagster import check
from dagster.core.definitions import ScheduleDefinition
from dagster.core.scheduler import RunningSchedule


def get_schedules(graphene_info):
    repository = graphene_info.context.get_handle().build_repository_definition()
    return [
        graphene_info.schema.type_named('ScheduleDefinition')(schedule_def=schedule_def)
        for schedule_def in repository.get_all_schedules()
    ]


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    scheduler = graphene_info.context.scheduler
    if not scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    runningSchedules = [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in scheduler.all_schedules()
    ]

    return graphene_info.schema.type_named('Scheduler')(runningSchedules=runningSchedules)


class DauphinSchedulerOrError(dauphin.Union):
    class Meta:
        name = 'SchedulerOrError'
        types = ('Scheduler', DauphinSchedulerNotDefinedError)


class DauphinScheduleDefinition(dauphin.ObjectType):
    class Meta:
        name = 'ScheduleDefinition'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params_string = dauphin.NonNull(dauphin.String)

    def __init__(self, schedule_def):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)

        super(DauphinScheduleDefinition, self).__init__(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            execution_params_string=json.dumps(schedule_def.execution_params),
        )


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta:
        name = 'RunningSchedule'

    schedule_id = dauphin.NonNull(dauphin.String)
    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    runs = dauphin.non_null_list('PipelineRun')

    def __init__(self, graphene_info, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', RunningSchedule)

        super(DauphinRunningSchedule, self).__init__(
            schedule_id=schedule.schedule_id,
            schedule_definition=graphene_info.schema.type_named('ScheduleDefinition')(
                schedule.schedule_definition
            ),
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )

    def resolve_runs(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.pipeline_runs.all_runs_for_pipeline(
                self._schedule.schedule_definition.execution_params['selector']['name']
            )
        ]


class DauphinScheduler(dauphin.ObjectType):
    class Meta:
        name = 'Scheduler'

    runningSchedules = dauphin.non_null_list('RunningSchedule')


class DauphinRunningScheduleInput(dauphin.InputObjectType):
    class Meta:
        name = 'RunningScheduleInput'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params = dauphin.NonNull('ExecutionParams')


class RunningScheduleResult(dauphin.ObjectType):
    class Meta:
        name = 'RunningScheduleResult'

    schedule = dauphin.NonNull('RunningSchedule')


class DauphinDeleteRunningScheduleResult(dauphin.ObjectType):
    class Meta:
        name = 'DeleteRunningScheduleResult'

    deleted_schedule = dauphin.NonNull('RunningSchedule')


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'StartScheduleMutation'

    class Arguments:
        schedule_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_id):
        scheduler = graphene_info.context.scheduler

        python_path = sys.executable
        handle = graphene_info.context.get_handle()
        repository_path = handle.data.repository_yaml

        schedule = scheduler.start_schedule(schedule_id, python_path, repository_path)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(schedule)
        )


class DauphinEndRunningScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'EndRunningScheduleMutation'

    class Arguments:
        schedule_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_id):
        scheduler = graphene_info.context.scheduler

        schedule = scheduler.end_schedule(schedule_id)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(schedule)
        )
