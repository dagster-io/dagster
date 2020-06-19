from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
)
from dagster.core.host_representation.handle import RepositoryHandle

from .utils import execute_unary_api_cli_command


def sync_get_external_partition_names(repository_handle, partition_set_name):
    from dagster.cli.api import PartitionNamesApiCommandArgs

    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    repository_origin = repository_handle.get_origin()
    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_names',
            PartitionNamesApiCommandArgs(
                repository_origin=repository_origin, partition_set_name=partition_set_name
            ),
        ),
        (ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_config(repository_handle, partition_set_name, partition_name):
    from dagster.cli.api import PartitionApiCommandArgs

    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_config',
            PartitionApiCommandArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
    )


def sync_get_external_partition_tags(repository_handle, partition_set_name, partition_name):
    from dagster.cli.api import PartitionApiCommandArgs

    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition_tags',
            PartitionApiCommandArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        (ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
    )
