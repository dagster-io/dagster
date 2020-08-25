from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.types import ExternalTriggeredExecutionArgs

from .utils import execute_unary_api_cli_command


def sync_get_external_trigger_execution_params(instance, repository_handle, trigger_name):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(trigger_name, "trigger_name")

    origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            origin.executable_path,
            "trigger_execution_params",
            ExternalTriggeredExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                trigger_name=trigger_name,
            ),
        ),
        (ExternalExecutionParamsData, ExternalExecutionParamsErrorData),
    )


def sync_get_external_trigger_execution_params_ephemeral_grpc(
    instance, repository_handle, trigger_name
):
    from dagster.grpc.client import ephemeral_grpc_api_client

    origin = repository_handle.get_origin()
    with ephemeral_grpc_api_client(
        LoadableTargetOrigin(executable_path=origin.executable_path)
    ) as api_client:
        return sync_get_external_trigger_execution_params_grpc(
            api_client, instance, repository_handle, trigger_name
        )


def sync_get_external_trigger_execution_params_grpc(
    api_client, instance, repository_handle, trigger_name
):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(trigger_name, "trigger_name")

    origin = repository_handle.get_origin()

    return check.inst(
        api_client.external_trigger_execution_params(
            external_triggered_execution_args=ExternalTriggeredExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                trigger_name=trigger_name,
            )
        ),
        (ExternalExecutionParamsData, ExternalExecutionParamsErrorData),
    )
