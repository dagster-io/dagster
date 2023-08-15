from dagster._api.snapshot_schedule import sync_get_external_schedule_execution_data_ephemeral_grpc
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.host_representation.external_data import ExternalScheduleExecutionErrorData
from dagster._core.test_utils import instance_for_test
from dagster._grpc.client import ephemeral_grpc_api_client
from dagster._grpc.types import ExternalScheduleExecutionArgs
from dagster._serdes import deserialize_value
from dagster._seven import get_current_datetime_in_utc

from .utils import get_bar_repo_handle


def test_external_schedule_execution_data_api_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "foo_schedule",
                None,
            )
            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.run_config == {"fizz": "buzz"}
            assert to_launch.tags == {"dagster/schedule_name": "foo_schedule"}


def test_external_schedule_execution_data_api_never_execute_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "foo_schedule_never_execute",
                None,
            )
            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 0


def test_external_schedule_execution_deserialize_error():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            origin = repository_handle.get_external_origin()
            with ephemeral_grpc_api_client(
                origin.code_location_origin.loadable_target_origin
            ) as api_client:
                result = deserialize_value(
                    api_client.external_schedule_execution(
                        external_schedule_execution_args=ExternalScheduleExecutionArgs(
                            repository_origin=origin,
                            instance_ref=instance.get_ref(),
                            schedule_name="foobar",
                            scheduled_execution_timestamp=None,
                        )._replace(repository_origin="INVALID")
                    )
                )
                assert isinstance(result, ExternalScheduleExecutionErrorData)


def test_include_execution_time_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_time = get_current_datetime_in_utc()
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "foo_schedule_echo_time",
                execution_time,
            )

            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.run_config == {"passed_in_time": execution_time.isoformat()}
            assert to_launch.tags == {"dagster/schedule_name": "foo_schedule_echo_time"}


def test_run_request_partition_key_schedule_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_time = get_current_datetime_in_utc()
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "partitioned_run_request_schedule",
                execution_time,
            )

            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.tags["dagster/schedule_name"] == "partitioned_run_request_schedule"
            assert to_launch.tags["dagster/partition"] == "a"
