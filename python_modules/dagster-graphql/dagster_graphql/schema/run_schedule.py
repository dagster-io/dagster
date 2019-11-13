import glob
import heapq
import json
import os

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
        types = ('Scheduler', DauphinSchedulerNotDefinedError, 'PythonError')


class DauphinScheduleDefinition(dauphin.ObjectType):
    class Meta:
        name = 'ScheduleDefinition'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params_string = dauphin.NonNull(dauphin.String)
    environment_config_yaml = dauphin.NonNull(dauphin.String)

    def resolve_environment_config_yaml(self, _graphene_info):
        environment_config = (
            self._schedule_def.execution_params['environmentConfigData']
            or self._schedule_def.environment_dict_fn()
        )

        environment_config_yaml = yaml.dump(environment_config, default_flow_style=False)
        return environment_config_yaml if environment_config_yaml else ''

    def __init__(self, schedule_def):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)

        execution_params = schedule_def.execution_params
        environment_dict_fn = schedule_def.environment_dict_fn
        if environment_dict_fn:
            execution_params['environmentConfigData'] = environment_dict_fn()

        super(DauphinScheduleDefinition, self).__init__(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            execution_params_string=seven.json.dumps(execution_params),
        )


class DauphinScheduleAttemptStatus(dauphin.Enum):
    class Meta:
        name = 'ScheduleAttemptStatus'

    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'


class DauphinScheduleAttempt(dauphin.ObjectType):
    class Meta:
        name = 'ScheduleAttempt'

    time = dauphin.NonNull(dauphin.String)
    json_result = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('ScheduleAttemptStatus')
    run = dauphin.Field('PipelineRun')


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta:
        name = 'RunningSchedule'

    id = dauphin.NonNull(dauphin.String)
    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    status = dauphin.NonNull('ScheduleStatus')
    runs = dauphin.Field(dauphin.non_null_list('PipelineRun'), limit=dauphin.Int())
    runs_count = dauphin.NonNull(dauphin.Int)
    attempts = dauphin.Field(dauphin.non_null_list('ScheduleAttempt'), limit=dauphin.Int())
    logs_path = dauphin.NonNull(dauphin.String)

    def __init__(self, graphene_info, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', Schedule)

        super(DauphinRunningSchedule, self).__init__(
            id=schedule.schedule_id,
            schedule_definition=graphene_info.schema.type_named('ScheduleDefinition')(
                get_dagster_schedule_def(graphene_info, schedule.name)
            ),
            status=schedule.status,
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )

    def resolve_attempts(self, graphene_info, **kwargs):
        limit = kwargs.get('limit')

        scheduler = graphene_info.context.get_scheduler()
        log_dir = scheduler.log_path_for_schedule(self._schedule.name)

        results = glob.glob(os.path.join(log_dir, "*.result"))
        latest_results = heapq.nlargest(limit, results, key=os.path.getctime)

        attempts = []
        for result_path in latest_results:
            with open(result_path, 'r') as f:
                line = f.readline()
                if not line:
                    continue  # File is empty

                start_scheduled_execution_response = json.loads(line)
                json_result = start_scheduled_execution_response['data']['startScheduledExecution']
                typename = json_result['__typename']

                if typename == 'StartPipelineExecutionSuccess':
                    status = DauphinScheduleAttemptStatus.SUCCESS
                elif typename == 'ScheduleExecutionBlocked':
                    status = DauphinScheduleAttemptStatus.SKIPPED
                else:
                    status = DauphinScheduleAttemptStatus.ERROR

                run = None
                if typename == 'StartPipelineExecutionSuccess':
                    run_id = json_result['run']['runId']
                    run = graphene_info.schema.type_named('PipelineRun')(
                        graphene_info.context.instance.get_run_by_id(run_id)
                    )

                attempts.append(
                    graphene_info.schema.type_named('ScheduleAttempt')(
                        time=os.path.getctime,
                        json_result=json.dumps(json_result),
                        status=status,
                        run=run,
                    )
                )

        return attempts

    def resolve_logs_path(self, graphene_info):
        scheduler = graphene_info.context.get_scheduler()
        return scheduler.log_path_for_schedule(self._schedule.name)

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs_with_matching_tags(
                [("dagster/schedule_id", self._schedule.schedule_id)], limit=kwargs.get('limit')
            )
        ]

    def resolve_runs_count(self, graphene_info):
        return graphene_info.context.instance.get_run_count_with_matching_tags(
            [("dagster/schedule_id", self._schedule.schedule_id)]
        )


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
