from dagster.api.snapshot_job import sync_get_external_job_params_ephemeral_grpc
from dagster.core.host_representation import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
)
from dagster.core.test_utils import instance_for_test

from .utils import get_bar_repo_handle


def test_external_job_error():
    with instance_for_test() as instance:
        with get_bar_repo_handle() as repository_handle:
            result = sync_get_external_job_params_ephemeral_grpc(
                instance, repository_handle, "job_error"
            )
            assert isinstance(result, ExternalExecutionParamsErrorData)
            assert "womp womp" in result.error.to_string()


def test_external_job_grpc():
    with instance_for_test() as instance:
        with get_bar_repo_handle() as repository_handle:
            result = sync_get_external_job_params_ephemeral_grpc(
                instance, repository_handle, "job_foo"
            )
            assert isinstance(result, ExternalExecutionParamsData)
            assert result.run_config == {"foo": "FOO"}
