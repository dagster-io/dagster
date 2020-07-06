from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.grpc.client import ephemeral_grpc_api_client
from dagster.grpc.types import PartitionArgs, PartitionNamesArgs

from .utils import execute_unary_api_cli_command


def sync_get_external_partition_names(repository_handle, partition_set_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_names',
            PartitionNamesArgs(
                repository_origin=repository_origin, partition_set_name=partition_set_name
            ),
        ),
        (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_names_grpc(repository_handle, partition_set_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    repository_origin = repository_handle.get_origin()

    with ephemeral_grpc_api_client(
        python_executable_path=repository_origin.executable_path
    ) as api_client:
        return check.inst(
            api_client.external_partition_names(
                partition_names_args=PartitionNamesArgs(
                    repository_origin=repository_origin, partition_set_name=partition_set_name,
                ),
            ),
            (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
        )


def sync_get_external_partition_config(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_config',
            PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_config_grpc(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    with ephemeral_grpc_api_client(
        python_executable_path=repository_origin.executable_path
    ) as api_client:
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
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_tags',
            PartitionArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_tags_grpc(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    with ephemeral_grpc_api_client(
        python_executable_path=repository_origin.executable_path
    ) as api_client:
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
