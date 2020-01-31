import heapq
import json
import os

import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import (
    get_dagster_schedule_def,
    get_schedule_attempt_filenames,
)
from dagster_graphql.schema.errors import (
    DauphinScheduleNotFoundError,
    DauphinSchedulerNotDefinedError,
)

from dagster import check, seven
from dagster.core.definitions import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.scheduler import Schedule


class DauphinScheduleStatus(dauphin.Enum):
    class Meta(object):
        name = 'ScheduleStatus'

    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ENDED = 'ENDED'


class DauphinSchedulerOrError(dauphin.Union):
    class Meta(object):
        name = 'SchedulerOrError'
        types = ('Scheduler', DauphinSchedulerNotDefinedError, 'PythonError')


class DauphinScheduleOrError(dauphin.Union):
    class Meta(object):
        name = 'ScheduleOrError'
        types = ('RunningSchedule', DauphinScheduleNotFoundError, 'PythonError')


class DauphinScheduleDefinition(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleDefinition'

    name = dauphin.NonNull(dauphin.String)
    cron_schedule = dauphin.NonNull(dauphin.String)
    execution_params_string = dauphin.NonNull(dauphin.String)
    environment_config_yaml = dauphin.NonNull(dauphin.String)

    def resolve_environment_config_yaml(self, _graphene_info):
        schedule_def = self._schedule_def
        environment_config = schedule_def.get_environment_dict(self._schedule_context)
        environment_config_yaml = yaml.dump(environment_config, default_flow_style=False)
        return environment_config_yaml if environment_config_yaml else ''

    def __init__(self, graphene_info, schedule_def):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)
        self._schedule_context = ScheduleExecutionContext(graphene_info.context.instance)
        execution_params = schedule_def.execution_params
        environment_config = schedule_def.get_environment_dict(self._schedule_context)
        execution_params['environmentConfigData'] = environment_config

        super(DauphinScheduleDefinition, self).__init__(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            execution_params_string=seven.json.dumps(execution_params),
        )


class DauphinScheduleAttemptStatus(dauphin.Enum):
    class Meta(object):
        name = 'ScheduleAttemptStatus'

    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'


class DauphinScheduleAttempt(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleAttempt'

    time = dauphin.NonNull(dauphin.Float)
    json_result = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('ScheduleAttemptStatus')
    run = dauphin.Field('PipelineRun')


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningSchedule'

    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    status = dauphin.NonNull('ScheduleStatus')
    runs = dauphin.Field(dauphin.non_null_list('PipelineRun'), limit=dauphin.Int())
    runs_count = dauphin.NonNull(dauphin.Int)
    attempts = dauphin.Field(dauphin.non_null_list('ScheduleAttempt'), limit=dauphin.Int())
    attempts_count = dauphin.NonNull(dauphin.Int)
    logs_path = dauphin.NonNull(dauphin.String)

    def __init__(self, graphene_info, schedule):
        self._schedule = check.inst_param(schedule, 'schedule', Schedule)

        super(DauphinRunningSchedule, self).__init__(
            schedule_definition=graphene_info.schema.type_named('ScheduleDefinition')(
                graphene_info=graphene_info,
                schedule_def=get_dagster_schedule_def(graphene_info, schedule.name),
            ),
            status=schedule.status,
            python_path=schedule.python_path,
            repository_path=schedule.repository_path,
        )

    def resolve_attempts(self, graphene_info, **kwargs):
        limit = kwargs.get('limit')

        results = get_schedule_attempt_filenames(graphene_info, self._schedule.name)
        if limit is None:
            limit = len(results)
        latest_results = heapq.nlargest(limit, results, key=os.path.getctime)

        attempts = []
        for result_path in latest_results:
            with open(result_path, 'r') as f:
                line = f.readline()
                if not line:
                    continue  # File is empty

                start_scheduled_execution_response = json.loads(line)
                run = None

                if 'errors' in start_scheduled_execution_response:
                    status = DauphinScheduleAttemptStatus.ERROR
                    json_result = start_scheduled_execution_response['errors']
                else:
                    json_result = start_scheduled_execution_response['data'][
                        'startScheduledExecution'
                    ]
                    typename = json_result['__typename']

                    if (
                        typename == 'StartPipelineExecutionSuccess'
                        or typename == 'LaunchPipelineExecutionSuccess'
                    ):
                        status = DauphinScheduleAttemptStatus.SUCCESS
                        run_id = json_result['run']['runId']
                        run = graphene_info.schema.type_named('PipelineRun')(
                            graphene_info.context.instance.get_run_by_id(run_id)
                        )
                    elif typename == 'ScheduleExecutionBlocked':
                        status = DauphinScheduleAttemptStatus.SKIPPED
                    else:
                        status = DauphinScheduleAttemptStatus.ERROR

                attempts.append(
                    graphene_info.schema.type_named('ScheduleAttempt')(
                        time=os.path.getctime(result_path),
                        json_result=json.dumps(json_result),
                        status=status,
                        run=run,
                    )
                )

        return attempts

    def resolve_attempts_count(self, graphene_info):
        attempt_files = get_schedule_attempt_filenames(graphene_info, self._schedule.name)
        return len(attempt_files)

    def resolve_logs_path(self, graphene_info):
        instance = graphene_info.context.instance
        repository = graphene_info.context.get_repository()
        return instance.log_path_for_schedule(repository, self._schedule.name)

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter(tags={'dagster/schedule_name': self._schedule.name}),
                limit=kwargs.get('limit'),
            )
        ]

    def resolve_runs_count(self, graphene_info):
        return graphene_info.context.instance.get_runs_count(
            filter=PipelineRunsFilter(tags=[("dagster/schedule_name", self._schedule.name)])
        )


class DauphinScheduler(dauphin.ObjectType):
    class Meta(object):
        name = 'Scheduler'

    runningSchedules = dauphin.non_null_list('RunningSchedule')


class RunningScheduleResult(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningScheduleResult'

    schedule = dauphin.NonNull('RunningSchedule')


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_name):
        repository = graphene_info.context.get_repository()
        instance = graphene_info.context.instance

        schedule = instance.start_schedule(repository, schedule_name)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(
                graphene_info, schedule=schedule
            )
        )


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StopRunningScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('RunningScheduleResult')

    def mutate(self, graphene_info, schedule_name):
        repository = graphene_info.context.get_repository()
        instance = graphene_info.context.instance

        schedule = instance.stop_schedule(repository, schedule_name)

        return graphene_info.schema.type_named('RunningScheduleResult')(
            schedule=graphene_info.schema.type_named('RunningSchedule')(
                graphene_info, schedule=schedule
            )
        )
