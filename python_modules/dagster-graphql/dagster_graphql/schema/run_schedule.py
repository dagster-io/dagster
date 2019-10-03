import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import get_dagster_schedule_def
from dagster_graphql.implementation.utils import UserFacingGraphQLError, capture_dauphin_error
from dagster_graphql.schema.errors import DauphinSchedulerNotDefinedError

from dagster import check, seven
from dagster.core.definitions import ScheduleDefinition
from dagster.core.scheduler import Schedule


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    scheduler = graphene_info.context.get_scheduler()
    if not scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    runningSchedules = [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in scheduler.all_schedules()
    ]

    return graphene_info.schema.type_named('Scheduler')(runningSchedules=runningSchedules)


class DauphinScheduleStatus(dauphin.Enum):
    class Meta:
        name = 'ScheduleStatus'

    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ENDED = 'ENDED'


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
    environment_config_yaml = dauphin.NonNull(dauphin.String)

    def resolve_environment_config_yaml(self, _graphene_info):
        environment_config = self._schedule_def.execution_params['environmentConfigData']
        environment_config_yaml = yaml.dump(environment_config, default_flow_style=False)
        return environment_config_yaml if environment_config_yaml else ''

    def __init__(self, schedule_def):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)

        super(DauphinScheduleDefinition, self).__init__(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            execution_params_string=seven.json.dumps(schedule_def.execution_params),
        )


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta:
        name = 'RunningSchedule'

    schedule_id = dauphin.NonNull(dauphin.String)
    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    status = dauphin.NonNull('ScheduleStatus')
    runs = dauphin.non_null_list('PipelineRun')
    logs_path = dauphin.NonNull(dauphin.String)

    def __init__(self, graphene_info, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', Schedule)

        super(DauphinRunningSchedule, self).__init__(
            schedule_id=schedule.schedule_id,
            schedule_definition=graphene_info.schema.type_named('ScheduleDefinition')(
                get_dagster_schedule_def(graphene_info, schedule.name)
            ),
            status=schedule.status,
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )

    def resolve_logs_path(self, graphene_info):
        scheduler = graphene_info.context.get_scheduler()
        return scheduler.log_path_for_schedule(self._schedule.name)

    def resolve_runs(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs_with_matching_tag(
                "dagster/schedule_id", self._schedule.schedule_id
            )
        ]


class DauphinScheduler(dauphin.ObjectType):
    class Meta:
        name = 'Scheduler'

    runningSchedules = dauphin.non_null_list('RunningSchedule')


class RunningScheduleResult(dauphin.ObjectType):
    class Meta:
        name = 'RunningScheduleResult'

    schedule = dauphin.NonNull('RunningSchedule')


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'StartScheduleMutation'

    class Arguments:
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_name):
        scheduler = graphene_info.context.get_scheduler()

        schedule = scheduler.start_schedule(schedule_name)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(
                graphene_info, schedule=schedule
            )
        )


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta:
        name = 'StopRunningScheduleMutation'

    class Arguments:
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_name):
        scheduler = graphene_info.context.get_scheduler()

        schedule = scheduler.stop_schedule(schedule_name)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(
                graphene_info, schedule=schedule
            )
        )
