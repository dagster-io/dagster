from dagster.api.snapshot_sensor import sync_get_external_sensor_execution_data_ephemeral_grpc
from dagster.core.host_representation.external_data import (
    ExternalSensorExecutionData,
    ExternalSensorExecutionErrorData,
)
from dagster.core.test_utils import instance_for_test

from .utils import get_bar_repo_handle


def test_external_sensor_grpc():
    with get_bar_repo_handle() as repository_handle:
        with instance_for_test() as instance:
            result = sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_foo", None
            )
            assert isinstance(result, ExternalSensorExecutionData)
            assert len(result.run_params) == 2
            run_params = result.run_params[0]
            assert run_params.run_config == {"foo": "FOO"}
            assert run_params.tags == {"foo": "foo_tag"}


def test_external_sensor_error():
    with get_bar_repo_handle() as repository_handle:
        with instance_for_test() as instance:
            result = sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_error", None
            )
            assert isinstance(result, ExternalSensorExecutionErrorData)
            assert "womp womp" in result.error.to_string()
