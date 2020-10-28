from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.types import ExternalJobArgs


def sync_get_external_job_params_ephemeral_grpc(instance, repository_handle, name):
    from dagster.grpc.client import ephemeral_grpc_api_client

    origin = repository_handle.get_origin()
    with ephemeral_grpc_api_client(
        LoadableTargetOrigin(executable_path=origin.executable_path)
    ) as api_client:
        return sync_get_external_job_params_grpc(api_client, instance, repository_handle, name)


def sync_get_external_job_params_grpc(api_client, instance, repository_handle, name):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(name, "name")

    origin = repository_handle.get_origin()

    return check.inst(
        api_client.external_job_params(
            external_job_args=ExternalJobArgs(
                repository_origin=origin, instance_ref=instance.get_ref(), name=name,
            )
        ),
        (ExternalExecutionParamsData, ExternalExecutionParamsErrorData),
    )
