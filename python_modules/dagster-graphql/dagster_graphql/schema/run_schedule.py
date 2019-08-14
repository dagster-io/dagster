import json
import sys

from dagster import check
from dagster_graphql import dauphin

from dagster_graphql.implementation.scheduler import RunSchedule, SystemCronScheduler


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
        graphene_info.schema.type_named('RunSchedule')(s) for s in scheduler.all_schedules()
    ]

    return graphene_info.schema.type_named('Scheduler')(
        scheduler_type=scheduler_type, schedules=schedules
    )


class DauphinRunSchedule(dauphin.ObjectType):
    class Meta:
        name = 'RunSchedule'

    schedule_id = dauphin.NonNull(dauphin.String)
    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params_string = dauphin.NonNull(dauphin.String)
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)

    def __init__(self, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', RunSchedule)

        super(DauphinRunSchedule, self).__init__(
            schedule_id=schedule.schedule_id,
            name=schedule.name,
            cron_schedule=schedule.cron_schedule,
            execution_params_string=json.dumps(schedule.execution_params),
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )


class SchedulerType(dauphin.Enum):
    SystemCronScheduler = "SystemCronScheduler"


class DauphinScheduler(dauphin.ObjectType):
    class Meta:
        name = 'Scheduler'

    scheduler_type = dauphin.NonNull(dauphin.String)
    schedules = dauphin.non_null_list('RunSchedule')


class DauphinRunScheduleInput(dauphin.InputObjectType):
    class Meta:
        name = 'RunScheduleInput'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params = dauphin.NonNull('ExecutionParams')


class RunScheduleResult(dauphin.ObjectType):
    class Meta:
        name = 'RunScheduleResult'

    schedule = dauphin.NonNull('RunSchedule')


class DauphinDeleteRunScheduleResult(dauphin.ObjectType):
    class Meta:
        name = 'DeleteRunScheduleResult'

    deleted_schedule = dauphin.NonNull('RunSchedule')


class DauphinCreateRunScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'CreateRunScheduleMutation'

    class Arguments:
        schedule = dauphin.NonNull('RunScheduleInput')

    Output = dauphin.NonNull('RunScheduleResult')

    def mutate(self, graphene_info, schedule):
        from dagster_graphql.schema.roots import create_execution_params

        # Check execution_params is valid ExecutionParams
        create_execution_params(schedule.get('execution_params'))

        scheduler = graphene_info.context.scheduler
        schedule = scheduler.create_schedule(
            name=schedule.get('name'),
            cron_schedule=schedule.get('cron_schedule'),
            execution_params=schedule.get('execution_params'),
        )

        return graphene_info.schema.type_named('RunScheduleResult')(
            schedule=graphene_info.schema.type_named('RunSchedule')(schedule)
        )


class DauphinStartRunScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'StartRunScheduleMutation'

    class Arguments:
        schedule_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunScheduleResult')

    def mutate(self, graphene_info, schedule_id):
        scheduler = graphene_info.context.scheduler

        python_path = sys.executable
        handle = graphene_info.context.get_handle()
        repository_path = handle.data.repository_yaml

        schedule = scheduler.start_schedule(schedule_id, python_path, repository_path)

        return graphene_info.schema.type_named('RunScheduleResult')(
            schedule=graphene_info.schema.type_named('RunSchedule')(schedule)
        )


class DauphinEndRunScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'EndRunSCheduleMutation'

    class Arguments:
        schedule_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunScheduleResult')

    def mutate(self, graphene_info, schedule_id):
        scheduler = graphene_info.context.scheduler

        schedule = scheduler.end_schedule(schedule_id)

        return graphene_info.schema.type_named('RunScheduleResult')(
            schedule=graphene_info.schema.type_named('RunSchedule')(schedule)
        )


class DauphineDeleteRunScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'DeleteRunScheduleMutation'

    class Arguments:
        schedule_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('DeleteRunScheduleResult')

    def mutate(self, graphene_info, schedule_id):
        scheduler = graphene_info.context.scheduler
        schedule = scheduler.remove_schedule(schedule_id)

        return graphene_info.schema.type_named('DeleteRunScheduleResult')(
            deleted_schedule=graphene_info.schema.type_named('RunSchedule')(schedule)
        )
