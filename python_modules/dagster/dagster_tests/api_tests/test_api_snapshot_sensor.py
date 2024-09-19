import os
from typing import Optional
from unittest import mock

import pytest
from dagster._api.snapshot_sensor import (
    sync_get_external_sensor_execution_data_ephemeral_grpc,
    sync_get_external_sensor_execution_data_grpc,
)
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.errors import DagsterUserCodeProcessError, DagsterUserCodeUnreachableError
from dagster._core.remote_representation.external_data import ExternalSensorExecutionErrorData
from dagster._grpc.client import ephemeral_grpc_api_client
from dagster._grpc.types import SensorExecutionArgs
from dagster._serdes import deserialize_value

from dagster_tests.api_tests.utils import get_bar_repo_handle


def test_external_sensor_grpc(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        result = sync_get_external_sensor_execution_data_ephemeral_grpc(
            instance, repository_handle, "sensor_foo", None, None, None, None
        )
        assert isinstance(result, SensorExecutionData)
        assert len(result.run_requests) == 2
        run_request = result.run_requests[0]
        assert run_request.run_config == {"foo": "FOO"}
        assert run_request.tags == {"foo": "foo_tag", "dagster/sensor_name": "sensor_foo"}


def test_external_sensor_grpc_fallback_to_streaming(instance):
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

                    result = sync_get_external_sensor_execution_data_grpc(
                        api_client,
                        instance,
                        repository_handle,
                        "sensor_foo",
                        None,
                        None,
                        None,
                        None,
                    )
                    assert isinstance(result, SensorExecutionData)
                    assert len(result.run_requests) == 2
                    run_request = result.run_requests[0]
                    assert run_request.run_config == {"foo": "FOO"}
                    assert run_request.tags == {
                        "foo": "foo_tag",
                        "dagster/sensor_name": "sensor_foo",
                    }


def test_external_sensor_error(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(DagsterUserCodeProcessError, match="womp womp"):
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_error", None, None, None, None
            )


@pytest.mark.parametrize(argnames="timeout", argvalues=[0, 1], ids=["zero", "nonzero"])
@pytest.mark.parametrize("env_var_default_val", [200, None], ids=["env-var-set", "env-var-not-set"])
def test_external_sensor_client_timeout(instance, timeout: int, env_var_default_val: Optional[int]):
    if env_var_default_val:
        os.environ["DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS"] = str(env_var_default_val)
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(
            DagsterUserCodeUnreachableError,
            match=f"The sensor tick timed out due to taking longer than {timeout} seconds to execute the sensor function.",
        ):
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance,
                repository_handle,
                "sensor_times_out",
                None,
                None,
                None,
                None,
                timeout=timeout,
            )


def test_external_sensor_deserialize_error(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        origin = repository_handle.get_external_origin()
        with ephemeral_grpc_api_client(
            origin.code_location_origin.loadable_target_origin
        ) as api_client:
            result = deserialize_value(
                api_client.external_sensor_execution(
                    sensor_execution_args=SensorExecutionArgs(
                        repository_origin=origin,
                        instance_ref=instance.get_ref(),
                        sensor_name="foo",
                        last_tick_completion_time=None,
                        last_run_key=None,
                        cursor=None,
                        last_sensor_start_time=None,
                    )
                )
            )
            assert isinstance(result, ExternalSensorExecutionErrorData)


def test_external_sensor_raises_dagster_error(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(DagsterUserCodeProcessError, match="Dagster error"):
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_raises_dagster_error", None, None, None, None
            )
