import heapq
import json
import os

import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import (
    get_dagster_schedule_def,
    get_schedule_attempt_filenames,
    start_schedule,
    stop_schedule,
)
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinScheduleNotFoundError,
    DauphinSchedulerNotDefinedError,
)

from dagster import check
from dagster.core.definitions import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.core.scheduler import Schedule, ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickStatsSnapshot
from dagster.core.storage.pipeline_run import PipelineRunsFilter


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

    pipeline_name = dauphin.NonNull(dauphin.String)
    solid_subset = dauphin.List(dauphin.String)
    mode = dauphin.NonNull(dauphin.String)
    environment_config_yaml = dauphin.Field(dauphin.String)
    partition_set = dauphin.Field('PartitionSet')

    def resolve_environment_config_yaml(self, _graphene_info):
        schedule_def = self._schedule_def
        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
                '{schedule_name}'.format(schedule_name=schedule_def.name),
            ):
                environment_config = schedule_def.get_environment_dict(self._schedule_context)
        except ScheduleExecutionError:
            return None

        environment_config_yaml = yaml.dump(environment_config, default_flow_style=False)
        return environment_config_yaml if environment_config_yaml else ''

    def resolve_partition_set(self, graphene_info):
        if isinstance(self._schedule_def, PartitionScheduleDefinition):
            return graphene_info.schema.type_named('PartitionSet')(
                self._schedule_def.get_partition_set()
            )

        return None

    def __init__(self, graphene_info, schedule_def):
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)
        self._schedule_context = ScheduleExecutionContext(
            graphene_info.context.instance, graphene_info.context.get_repository()
        )
        self._schedule_def = check.inst_param(schedule_def, 'schedule_def', ScheduleDefinition)

        super(DauphinScheduleDefinition, self).__init__(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            pipeline_name=schedule_def.selector.name,
            solid_subset=schedule_def.selector.solid_subset,
            mode=schedule_def.mode,
        )


# TODO: Delete in 0.8.0 release
# https://github.com/dagster-io/dagster/issues/2288
class DauphinScheduleAttemptStatus(dauphin.Enum):
    class Meta(object):
        name = 'ScheduleAttemptStatus'

    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'


# TODO: Delete in 0.8.0 release
# https://github.com/dagster-io/dagster/issues/228
class DauphinScheduleAttempt(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleAttempt'

    time = dauphin.NonNull(dauphin.Float)
    json_result = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('ScheduleAttemptStatus')
    run = dauphin.Field('PipelineRun')


DauphinScheduleTickStatus = dauphin.Enum.from_enum(ScheduleTickStatus)


class DauphinScheduleTick(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTick'

    tick_id = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull('ScheduleTickStatus')
    timestamp = dauphin.NonNull(dauphin.Float)
    tick_specific_data = dauphin.Field('ScheduleTickSpecificData')


class DauphinScheduleTickSuccessData(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickSuccessData'

    run = dauphin.Field('PipelineRun')


class DauphinScheduleTickFailureData(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickFailureData'

    error = dauphin.NonNull('PythonError')


class DauphinScheduleTickSpecificData(dauphin.Union):
    class Meta(object):
        name = 'ScheduleTickSpecificData'
        types = (
            DauphinScheduleTickSuccessData,
            DauphinScheduleTickFailureData,
        )


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    if tick.status == ScheduleTickStatus.SUCCESS:
        run_id = tick.run_id
        run = None
        if graphene_info.context.instance.has_run(run_id):
            run = graphene_info.schema.type_named('PipelineRun')(
                graphene_info.context.instance.get_run_by_id(run_id)
            )
        return graphene_info.schema.type_named('ScheduleTickSuccessData')(run=run)
    elif tick.status == ScheduleTickStatus.FAILURE:
        error = tick.error
        return graphene_info.schema.type_named('ScheduleTickFailureData')(error=error)


class DauphinScheduleTickStatsSnapshot(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleTickStatsSnapshot'

    ticks_started = dauphin.NonNull(dauphin.Int)
    ticks_succeeded = dauphin.NonNull(dauphin.Int)
    ticks_skipped = dauphin.NonNull(dauphin.Int)
    ticks_failed = dauphin.NonNull(dauphin.Int)

    def __init__(self, stats):
        super(DauphinScheduleTickStatsSnapshot, self).__init__(
            ticks_started=stats.ticks_started,
            ticks_succeeded=stats.ticks_succeeded,
            ticks_skipped=stats.ticks_skipped,
            ticks_failed=stats.ticks_failed,
        )
        self._stats = check.inst_param(stats, 'stats', ScheduleTickStatsSnapshot)


class DauphinRunningSchedule(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningSchedule'

    schedule_definition = dauphin.NonNull('ScheduleDefinition')
    python_path = dauphin.Field(dauphin.String)
    repository_path = dauphin.Field(dauphin.String)
    status = dauphin.NonNull('ScheduleStatus')
    runs = dauphin.Field(dauphin.non_null_list('PipelineRun'), limit=dauphin.Int())
    runs_count = dauphin.NonNull(dauphin.Int)
    ticks = dauphin.Field(dauphin.non_null_list('ScheduleTick'), limit=dauphin.Int())
    ticks_count = dauphin.NonNull(dauphin.Int)
    stats = dauphin.NonNull('ScheduleTickStatsSnapshot')
    # TODO: Delete attempts and attempts_count in 0.8.0 release
    # https://github.com/dagster-io/dagster/issues/228
    attempts = dauphin.Field(dauphin.non_null_list('ScheduleAttempt'), limit=dauphin.Int())
    attempts_count = dauphin.NonNull(dauphin.Int)
    logs_path = dauphin.NonNull(dauphin.String)
    running_job_count = dauphin.NonNull(dauphin.Int)

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

    def resolve_running_job_count(self, graphene_info):
        repository = graphene_info.context.get_repository()
        running_job_count = graphene_info.context.instance.running_job_count(
            repository.name, self._schedule.name
        )
        return running_job_count

    # TODO: Delete in 0.8.0 release
    # https://github.com/dagster-io/dagster/issues/228
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
                        typename == 'StartPipelineRunSuccess'
                        or typename == 'LaunchPipelineRunSuccess'
                    ):
                        status = DauphinScheduleAttemptStatus.SUCCESS
                        run_id = json_result['run']['runId']
                        if graphene_info.context.instance.has_run(run_id):
                            run = graphene_info.schema.type_named('PipelineRun')(
                                graphene_info.context.instance.get_run_by_id(run_id)
                            )
                    elif typename == 'ScheduledExecutionBlocked':
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

    # TODO: Delete in 0.8.0 release
    # https://github.com/dagster-io/dagster/issues/228
    def resolve_attempts_count(self, graphene_info):
        attempt_files = get_schedule_attempt_filenames(graphene_info, self._schedule.name)
        return len(attempt_files)

    # TODO: Delete in 0.8.0 release
    # https://github.com/dagster-io/dagster/issues/228
    def resolve_logs_path(self, graphene_info):
        instance = graphene_info.context.instance
        repository = graphene_info.context.get_repository()
        return instance.logs_directory_for_schedule(repository, self._schedule.name)

    def resolve_stats(self, graphene_info):
        repository = graphene_info.context.get_repository()
        stats = graphene_info.context.instance.get_schedule_tick_stats_by_schedule(
            repository, self._schedule.name
        )
        return graphene_info.schema.type_named('ScheduleTickStatsSnapshot')(stats)

    def resolve_ticks(self, graphene_info, limit=None):

        repository = graphene_info.context.get_repository()

        # TODO: Add cursor limit argument to get_schedule_ticks_by_schedule
        # https://github.com/dagster-io/dagster/issues/2291
        ticks = graphene_info.context.instance.get_schedule_ticks_by_schedule(
            repository, self._schedule.name
        )

        if not limit:
            tick_subset = ticks
        else:
            tick_subset = ticks[:limit]

        return [
            graphene_info.schema.type_named('ScheduleTick')(
                tick_id=tick.tick_id,
                status=tick.status,
                timestamp=tick.timestamp,
                tick_specific_data=tick_specific_data_from_dagster_tick(graphene_info, tick),
            )
            for tick in tick_subset
        ]

    def resolve_ticks_count(self, graphene_info):
        repository = graphene_info.context.get_repository()
        ticks = graphene_info.context.instance.get_schedule_ticks_by_schedule(
            repository, self._schedule.name
        )
        return len(ticks)

    def resolve_runs(self, graphene_info, **kwargs):
        return [
            graphene_info.schema.type_named('PipelineRun')(r)
            for r in graphene_info.context.instance.get_runs(
                filters=PipelineRunsFilter.for_schedule(self._schedule), limit=kwargs.get('limit'),
            )
        ]

    def resolve_runs_count(self, graphene_info):
        return graphene_info.context.instance.get_runs_count(
            filters=PipelineRunsFilter.for_schedule(self._schedule)
        )


class DauphinScheduler(dauphin.ObjectType):
    class Meta(object):
        name = 'Scheduler'

    runningSchedules = dauphin.non_null_list('RunningSchedule')


class DauphinRunningScheduleResult(dauphin.ObjectType):
    class Meta(object):
        name = 'RunningScheduleResult'

    schedule = dauphin.NonNull('RunningSchedule')


class DauphinScheduleMutationResult(dauphin.Union):
    class Meta(object):
        name = 'ScheduleMutationResult'
        types = (DauphinPythonError, DauphinRunningScheduleResult)


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('ScheduleMutationResult')

    def mutate(self, graphene_info, schedule_name):
        return start_schedule(graphene_info, schedule_name)


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StopRunningScheduleMutation'

    class Arguments(object):
        schedule_name = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('ScheduleMutationResult')

    def mutate(self, graphene_info, schedule_name):
        return stop_schedule(graphene_info, schedule_name)
