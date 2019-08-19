import json
import sys

from dagster import check, ScheduleDefinition
from dagster_graphql import dauphin

from dagster.core.scheduler import RunningSchedule, SystemCronScheduler


def get_scheduler(graphene_info):
    scheduler = graphene_info.context.scheduler

    if isinstance(scheduler, SystemCronScheduler):
        scheduler_type = SchedulerType.SystemCronScheduler
    else:
        raise Exception(
            'Unknown Scheduler type {typ}. Add this Scheduler type to the SchedulerType '
            'GraphQL Enum'.format(typ=type(scheduler))
        )

    schedules = [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in scheduler.all_schedules()
    ]

    return graphene_info.schema.type_named('Scheduler')(
        scheduler_type=scheduler_type, schedules=schedules
    )


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


class SchedulerType(dauphin.Enum):
    SystemCronScheduler = "SystemCronScheduler"


class DauphinScheduler(dauphin.ObjectType):
    class Meta:
        name = 'Scheduler'

    scheduler_type = dauphin.NonNull(dauphin.String)
    schedules = dauphin.non_null_list('RunningSchedule')


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
