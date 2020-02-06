import uuid

from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils import file_relative_path

from .execution_queries import START_SCHEDULED_EXECUTION_QUERY
from .utils import InMemoryRunLauncher


def test_basic_start_scheduled_execution():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
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
    test_queue = InMemoryRunLauncher()

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(temp_dir),
            run_launcher=test_queue,
        )

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
        instance = DagsterInstance.local_temp(temp_dir)
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
        instance = DagsterInstance.local_temp(temp_dir)
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
        instance = DagsterInstance.local_temp(temp_dir)
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
        instance = DagsterInstance.local_temp(temp_dir)
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
        instance = DagsterInstance.local_temp(temp_dir)
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


def test_partition_based_multi_mode_decorator():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
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
