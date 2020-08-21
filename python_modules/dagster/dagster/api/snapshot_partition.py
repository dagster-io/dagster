from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.grpc.types import PartitionArgs, PartitionNamesArgs, PartitionSetExecutionParamArgs

from .utils import execute_unary_api_cli_command


def sync_get_external_partition_names(repository_handle, partition_set_name):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            "partition_names",
            PartitionNamesArgs(
                repository_origin=repository_origin, partition_set_name=partition_set_name
            ),
        ),
        (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_names_grpc(api_client, repository_handle, partition_set_name):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    repository_origin = repository_handle.get_origin()
    return check.inst(
        api_client.external_partition_names(
            partition_names_args=PartitionNamesArgs(
                repository_origin=repository_origin, partition_set_name=partition_set_name,
            ),
        ),
        (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_config(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            "partition_config",
            PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_config_grpc(
    api_client, repository_handle, partition_set_name, partition_name
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")
    repository_origin = repository_handle.get_origin()
    return check.inst(
        api_client.external_partition_config(
            partition_args=PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_tags(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            "partition_tags",
            PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_tags_grpc(
    api_client, repository_handle, partition_set_name, partition_name
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.str_param(partition_name, "partition_name")

    repository_origin = repository_handle.get_origin()
    return check.inst(
        api_client.external_partition_tags(
            partition_args=PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_set_execution_param_data(
    repository_handle, partition_set_name, partition_names
):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.list_param(partition_names, "partition_names", of_type=str)

    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            "partition_set_execution_param_data",
            PartitionSetExecutionParamArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_names=partition_names,
            ),
        ),
        (ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_set_execution_param_data_grpc(
    api_client, repository_handle, partition_set_name, partition_names
):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.list_param(partition_names, "partition_names", of_type=str)

    repository_origin = repository_handle.get_origin()

    return check.inst(
        api_client.external_partition_set_execution_params(
            partition_set_execution_param_args=PartitionSetExecutionParamArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_names=partition_names,
            ),
        ),
        (ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData),
    )
