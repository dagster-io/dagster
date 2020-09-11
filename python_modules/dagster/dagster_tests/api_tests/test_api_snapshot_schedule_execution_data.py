import pytest

from dagster import seven
from dagster.api.snapshot_schedule import (
    sync_get_external_schedule_execution_data,
    sync_get_external_schedule_execution_data_ephemeral_grpc,
)
from dagster.core.host_representation.external_data import ExternalScheduleExecutionData
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import instance_for_test
from dagster.grpc.types import ScheduleExecutionDataMode
from dagster.seven import get_current_datetime_in_utc

from .utils import get_bar_repo_handle


@pytest.mark.parametrize("schedule_name", ["foo_schedule", "foo_schedule_never_execute"])
def test_external_schedule_execution_data_api_preview(schedule_name):
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data(
            instance, repository_handle, schedule_name, ScheduleExecutionDataMode.PREVIEW, None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)

        assert execution_data.run_config == {"fizz": "buzz"}
        assert execution_data.tags == {"dagster/schedule_name": schedule_name}
        assert execution_data.should_execute is None


def test_external_schedule_execution_data_api_launch():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data(
            instance,
            repository_handle,
            "foo_schedule",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {"fizz": "buzz"}
        assert execution_data.tags == {"dagster/schedule_name": "foo_schedule"}
        assert execution_data.should_execute == True


def test_external_schedule_execution_data_api_never_execute():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data(
            instance,
            repository_handle,
            "foo_schedule_never_execute",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {}
        assert execution_data.tags == {}
        assert execution_data.should_execute == False


@pytest.mark.parametrize("schedule_name", ["foo_schedule", "foo_schedule_never_execute"])
def test_external_schedule_execution_data_api_preview_grpc(schedule_name):
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
            instance, repository_handle, schedule_name, ScheduleExecutionDataMode.PREVIEW, None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)

        assert execution_data.run_config == {"fizz": "buzz"}
        assert execution_data.tags == {"dagster/schedule_name": schedule_name}
        assert execution_data.should_execute is None


def test_external_schedule_execution_data_api_grpc():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
            instance,
            repository_handle,
            "foo_schedule",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {"fizz": "buzz"}
        assert execution_data.tags == {"dagster/schedule_name": "foo_schedule"}
        assert execution_data.should_execute == True


def test_external_schedule_execution_data_api_never_execute_grpc():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
            instance,
            repository_handle,
            "foo_schedule_never_execute",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            None,
        )
        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {}
        assert execution_data.tags == {}
        assert execution_data.should_execute == False


def test_include_execution_time():
    repository_handle = get_bar_repo_handle()

    execution_time = get_current_datetime_in_utc()
    with instance_for_test() as instance:
        execution_data = sync_get_external_schedule_execution_data(
            instance,
            repository_handle,
            "foo_schedule_echo_time",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            execution_time,
        )

        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {"passed_in_time": execution_time.isoformat()}
        assert execution_data.tags == {"dagster/schedule_name": "foo_schedule_echo_time"}
        assert execution_data.should_execute == True


def test_include_execution_time_grpc():
    repository_handle = get_bar_repo_handle()

    execution_time = get_current_datetime_in_utc()
    with instance_for_test() as instance:
        execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
            instance,
            repository_handle,
            "foo_schedule_echo_time",
            ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
            execution_time,
        )

        assert isinstance(execution_data, ExternalScheduleExecutionData)
        assert execution_data.run_config == {"passed_in_time": execution_time.isoformat()}
        assert execution_data.tags == {"dagster/schedule_name": "foo_schedule_echo_time"}
        assert execution_data.should_execute == True
