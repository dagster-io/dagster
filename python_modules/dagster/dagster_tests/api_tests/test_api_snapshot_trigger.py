from dagster import seven
from dagster.api.snapshot_trigger import (
    sync_get_external_trigger_execution_params,
    sync_get_external_trigger_execution_params_ephemeral_grpc,
)
from dagster.core.host_representation import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
)
from dagster.core.instance import DagsterInstance

from .utils import get_bar_repo_handle


def test_external_trigger():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        result = sync_get_external_trigger_execution_params(
            instance, repository_handle, "triggered_foo"
        )
        assert isinstance(result, ExternalExecutionParamsData)
        assert result.run_config == {"foo": "FOO"}


def test_external_trigger_error():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        result = sync_get_external_trigger_execution_params(
            instance, repository_handle, "triggered_error"
        )
        assert isinstance(result, ExternalExecutionParamsErrorData)
        assert "womp womp" in result.error.to_string()


def test_external_trigger_grpc():
    repository_handle = get_bar_repo_handle()
    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance.local_temp(temp_dir)
        result = sync_get_external_trigger_execution_params_ephemeral_grpc(
            instance, repository_handle, "triggered_foo"
        )
        assert isinstance(result, ExternalExecutionParamsData)
        assert result.run_config == {"foo": "FOO"}
