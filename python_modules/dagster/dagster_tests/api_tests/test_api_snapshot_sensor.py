import pytest

from dagster._api.snapshot_sensor import sync_get_external_sensor_execution_data_ephemeral_grpc
from dagster.core.definitions.sensor_definition import SensorExecutionData
from dagster.core.errors import DagsterUserCodeProcessError

from .utils import get_bar_repo_handle


def test_external_sensor_grpc(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        result = sync_get_external_sensor_execution_data_ephemeral_grpc(
            instance, repository_handle, "sensor_foo", None, None, None
        )
        assert isinstance(result, SensorExecutionData)
        assert len(result.run_requests) == 2
        run_request = result.run_requests[0]
        assert run_request.run_config == {"foo": "FOO"}
        assert run_request.tags == {"foo": "foo_tag"}


def test_external_sensor_error(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(DagsterUserCodeProcessError, match="womp womp"):
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_error", None, None, None
            )


def test_external_sensor_raises_dagster_error(instance):
    with get_bar_repo_handle(instance) as repository_handle:
        with pytest.raises(DagsterUserCodeProcessError, match="Dagster error"):
            sync_get_external_sensor_execution_data_ephemeral_grpc(
                instance, repository_handle, "sensor_raises_dagster_error", None, None, None
            )
