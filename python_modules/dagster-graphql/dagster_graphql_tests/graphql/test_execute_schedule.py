import sys
import uuid

import pytest
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import check, seven
from dagster.core.instance import DagsterInstance
from dagster.utils import script_relative_path

from .execution_queries import START_SCHEDULED_EXECUTION_QUERY
from .setup import define_context_for_repository_yaml


def test_basic_start_scheduled_execution():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        context = define_context_for_repository_yaml(
            path=script_relative_path('../repository.yaml'), instance=instance
        )

        scheduler_handle = context.scheduler_handle
        scheduler_handle.up(python_path=sys.executable, repository_path=script_relative_path('../'))

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


def test_start_scheduled_execution_with_predefined_schedule_id_tag():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        context = define_context_for_repository_yaml(
            path=script_relative_path('../repository.yaml'), instance=instance
        )

        scheduler_handle = context.scheduler_handle
        scheduler_handle.up(python_path=sys.executable, repository_path=script_relative_path('../'))

        with pytest.raises(check.CheckError) as exc:
            execute_dagster_graphql(
                context,
                START_SCHEDULED_EXECUTION_QUERY,
                variables={
                    'scheduleName': 'no_config_pipeline_hourly_schedule_with_schedule_id_tag'
                },
            )

        assert (
            str(exc.value) == 'Invariant failed. Description: Tag dagster/schedule_id tag is '
            'already defined in executionMetadata.tags'
        )


def test_start_scheduled_execution_with_should_execute():
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        context = define_context_for_repository_yaml(
            path=script_relative_path('../repository.yaml'), instance=instance
        )

        scheduler_handle = context.scheduler_handle
        scheduler_handle.up(python_path=sys.executable, repository_path=script_relative_path('../'))

        result = execute_dagster_graphql(
            context,
            START_SCHEDULED_EXECUTION_QUERY,
            variables={'scheduleName': 'no_config_should_execute'},
        )

        assert not result.errors
        assert result.data

        assert result.data['startScheduledExecution']['__typename'] == 'ScheduledExecutionBlocked'
