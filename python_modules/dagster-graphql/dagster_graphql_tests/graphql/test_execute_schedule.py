import time
import uuid

import pytest
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.scheduler.scheduler import ScheduleTickStatus
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.schedules.sqlite import SqliteScheduleStorage
from dagster.utils import file_relative_path

from .execution_queries import START_SCHEDULED_EXECUTION_QUERY
from .utils import InMemoryRunLauncher


def get_instance(temp_dir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
        compute_log_manager=NoOpComputeLogManager(temp_dir),
    )


def get_instance_with_launcher(temp_dir):
    test_queue = InMemoryRunLauncher()

    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        schedule_storage=SqliteScheduleStorage.from_local(temp_dir),
        compute_log_manager=NoOpComputeLogManager(temp_dir),
        run_launcher=test_queue,
    )


def test_basic_start_scheduled_execution():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_pipeline_hourly_schedule'},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )

        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name']
            == 'no_config_pipeline'
        )

        assert any(
            tag['key'] == 'dagster/schedule_name'
            and tag['value'] == 'no_config_pipeline_hourly_schedule'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )


def test_basic_start_scheduled_execution_with_run_launcher():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance_with_launcher(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_pipeline_hourly_schedule'},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startScheduledExecution']['__typename'] == 'LaunchPipelineExecutionSuccess'
        )

        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name']
            == 'no_config_pipeline'
        )

        assert any(
            tag['key'] == 'dagster/schedule_name'
            and tag['value'] == 'no_config_pipeline_hourly_schedule'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )


def test_basic_start_scheduled_execution_with_environment_dict_fn():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_pipeline_hourly_schedule_with_config_fn'},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )

        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name']
            == 'no_config_pipeline'
        )

        assert any(
            tag['key'] == 'dagster/schedule_name'
            and tag['value'] == 'no_config_pipeline_hourly_schedule_with_config_fn'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )


def test_start_scheduled_execution_with_should_execute():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_should_execute'},
        )

        assert not result.errors
        assert result.data

        assert result.data['startScheduledExecution']['__typename'] == 'ScheduledExecutionBlocked'


def test_partition_based_execution():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context, START_SCHEDULED_EXECUTION_QUERY, variables={'scheduleName': 'partition_based'},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )

        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name']
            == 'no_config_pipeline'
        )

        tags = result.data['startScheduledExecution']['run']['tags']

        assert any(
            tag['key'] == 'dagster/schedule_name' and tag['value'] == 'partition_based'
            for tag in tags
        )

        assert any(tag['key'] == 'dagster/partition' and tag['value'] == '9' for tag in tags)
        assert any(
            tag['key'] == 'dagster/partition_set' and tag['value'] == 'scheduled_integer_partitions'
            for tag in tags
        )

        result_two = execute_dagster_graphql(
            context, START_SCHEDULED_EXECUTION_QUERY, variables={'scheduleName': 'partition_based'},
        )
        tags = result_two.data['startScheduledExecution']['run']['tags']
        # the last partition is selected on subsequent runs
        assert any(tag['key'] == 'dagster/partition' and tag['value'] == '9' for tag in tags)


def test_partition_based_custom_selector():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'partition_based_custom_selector'},
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name']
            == 'no_config_pipeline'
        )
        tags = result.data['startScheduledExecution']['run']['tags']
        assert any(
            tag['key'] == 'dagster/schedule_name'
            and tag['value'] == 'partition_based_custom_selector'
            for tag in tags
        )
        assert any(tag['key'] == 'dagster/partition' and tag['value'] == '9' for tag in tags)
        assert any(
            tag['key'] == 'dagster/partition_set' and tag['value'] == 'scheduled_integer_partitions'
            for tag in tags
        )

        result_two = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'partition_based_custom_selector'},
        )
        tags = result_two.data['startScheduledExecution']['run']['tags']
        # get a different partition based on the subsequent run storage
        assert any(tag['key'] == 'dagster/partition' and tag['value'] == '8' for tag in tags)


def test_partition_based_decorator():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'partition_based_decorator'},
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )


@pytest.mark.parametrize(
    'schedule_name',
    [
        'solid_subset_hourly_decorator',
        'solid_subset_daily_decorator',
        'solid_subset_monthly_decorator',
        'solid_subset_weekly_decorator',
    ],
)
def test_solid_subset_schedule_decorator(schedule_name):
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context, START_SCHEDULED_EXECUTION_QUERY, variables={'scheduleName': schedule_name},
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        execution_step_names = [
            log['step']['key']
            for log in result.data['startScheduledExecution']['run']['logs']['nodes']
            if log['__typename'] == 'ExecutionStepStartEvent'
        ]
        assert execution_step_names == ['return_foo.compute']


def test_partition_based_multi_mode_decorator():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'partition_based_multi_mode_decorator'},
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )


# Tests for ticks and execution user error boundary
def test_tick_success():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )
        repository = context.get_repository()

        schedule_handle = context.scheduler_handle
        schedule_def = schedule_handle.get_schedule_def_by_name(
            "no_config_pipeline_hourly_schedule"
        )

        start_time = time.time()
        execute_dagster_graphql(
            context, START_SCHEDULED_EXECUTION_QUERY, variables={'scheduleName': schedule_def.name},
        )

        ticks = instance.get_schedule_ticks_by_schedule(repository, schedule_def.name)

        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.schedule_name == schedule_def.name
        assert tick.cron_schedule == schedule_def.cron_schedule
        assert tick.timestamp > start_time and tick.timestamp < time.time()
        assert tick.status == ScheduleTickStatus.SUCCESS
        assert tick.run_id


def test_tick_skip():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )
        repository = context.get_repository()

        execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_should_execute'},
        )

        ticks = instance.get_schedule_ticks_by_schedule(repository, 'no_config_should_execute')

        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.status == ScheduleTickStatus.SKIPPED


def test_should_execute_scheduler_error():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )
        repository = context.get_repository()

        execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'should_execute_error_schedule'},
        )

        ticks = instance.get_schedule_ticks_by_schedule(repository, 'should_execute_error_schedule')

        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.status == ScheduleTickStatus.FAILURE
        assert tick.error
        assert (
            "Error occurred during the execution should_execute for schedule "
            "should_execute_error_schedule" in tick.error.message
        )


def test_tags_scheduler_error():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )
        repository = context.get_repository()

        execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'tags_error_schedule'},
        )

        ticks = instance.get_schedule_ticks_by_schedule(repository, 'tags_error_schedule')

        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.status == ScheduleTickStatus.FAILURE
        assert tick.error
        assert (
            "Error occurred during the execution of tags_fn for schedule tags_error_schedule"
            in tick.error.message
        )


def test_enviornment_dict_scheduler_error():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )
        repository = context.get_repository()

        execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'environment_dict_error_schedule'},
        )

        ticks = instance.get_schedule_ticks_by_schedule(
            repository, 'environment_dict_error_schedule'
        )

        assert len(ticks) == 1
        tick = ticks[0]
        assert tick.status == ScheduleTickStatus.FAILURE
        assert tick.error
        assert (
            "Error occurred during the execution of environment_dict_fn for schedule "
            "environment_dict_error_schedule" in tick.error.message
        )


def test_tagged_pipeline_schedule():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'tagged_pipeline_schedule'},
        )

        assert not result.errors
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name'] == 'tagged_pipeline'
        )

        assert any(
            tag['key'] == 'foo' and tag['value'] == 'bar'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )


def test_tagged_pipeline_override_schedule():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'tagged_pipeline_override_schedule'},
        )

        assert not result.errors
        assert (
            result.data['startScheduledExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name'] == 'tagged_pipeline'
        )

        assert not any(
            tag['key'] == 'foo' and tag['value'] == 'bar'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )
        assert any(
            tag['key'] == 'foo' and tag['value'] == 'notbar'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )


def test_tagged_pipeline_scheduled_execution_with_run_launcher():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance_with_launcher(temp_dir)
        context = define_context_for_repository_yaml(
            path=file_relative_path(__file__, '../repository.yaml'), instance=instance
        )

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'tagged_pipeline_schedule'},
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startScheduledExecution']['__typename'] == 'LaunchPipelineExecutionSuccess'
        )

        assert uuid.UUID(result.data['startScheduledExecution']['run']['runId'])
        assert (
            result.data['startScheduledExecution']['run']['pipeline']['name'] == 'tagged_pipeline'
        )

        assert any(
            tag['key'] == 'foo' and tag['value'] == 'bar'
            for tag in result.data['startScheduledExecution']['run']['tags']
        )
