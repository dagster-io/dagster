import os
import time
from typing import Optional
from unittest import mock

import pytest
from dagster._api.snapshot_schedule import (
    sync_get_external_schedule_execution_data_ephemeral_grpc,
    sync_get_external_schedule_execution_data_grpc,
)
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.remote_representation.external_data import ExternalScheduleExecutionErrorData
from dagster._core.test_utils import instance_for_test
from dagster._grpc.client import ephemeral_grpc_api_client
from dagster._grpc.types import ExternalScheduleExecutionArgs
from dagster._serdes import deserialize_value
from dagster._time import get_current_datetime

from dagster_tests.api_tests.utils import get_bar_repo_handle


def test_external_schedule_execution_data_api_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "foo_schedule",
                None,
                None,
            )
            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.run_config == {"fizz": "buzz"}
            assert to_launch.tags == {"dagster/schedule_name": "foo_schedule"}


@pytest.mark.parametrize("env_var_default_val", [200, None], ids=["env-var-set", "env-var-not-set"])
def test_external_schedule_client_timeout(instance, env_var_default_val: Optional[int]):
    if env_var_default_val:
        os.environ["DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS"] = str(env_var_default_val)
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(
            DagsterUserCodeUnreachableError,
            match="User code server request timed out due to taking longer than 1 seconds to complete.",
        ):
            sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance, repository_handle, "schedule_times_out", None, None, timeout=1
            )


def test_external_schedule_execution_data_api_grpc_fallback_to_streaming():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            origin = repository_handle.get_external_origin()
            with ephemeral_grpc_api_client(
                origin.code_location_origin.loadable_target_origin
            ) as api_client:
                with mock.patch("dagster._grpc.client.DagsterGrpcClient._query") as mock_method:
                    with mock.patch(
                        "dagster._grpc.client.DagsterGrpcClient._is_unimplemented_error",
                        return_value=True,
                    ):
                        my_exception = Exception("Unimplemented")
                        mock_method.side_effect = my_exception

                        execution_data = sync_get_external_schedule_execution_data_grpc(
                            api_client,
                            instance,
                            repository_handle,
                            "foo_schedule",
                            None,
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
            execution_time = get_current_datetime()

            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "foo_schedule_echo_time",
                TimestampWithTimezone(execution_time.timestamp(), "UTC"),
                None,
            )

            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.run_config == {"passed_in_time": execution_time.isoformat()}
            assert to_launch.tags == {"dagster/schedule_name": "foo_schedule_echo_time"}


def test_run_request_partition_key_schedule_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle(instance) as repository_handle:
            execution_data = sync_get_external_schedule_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "partitioned_run_request_schedule",
                TimestampWithTimezone(time.time(), "UTC"),
                None,
            )

            assert isinstance(execution_data, ScheduleExecutionData)
            assert len(execution_data.run_requests) == 1
            to_launch = execution_data.run_requests[0]
            assert to_launch.tags["dagster/schedule_name"] == "partitioned_run_request_schedule"
            assert to_launch.tags["dagster/partition"] == "a"
