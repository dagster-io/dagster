from dagster import check
from dagster.core.host_representation.external_data import ExternalPartitionData
from dagster.core.host_representation.handle import RepositoryHandle

from .utils import execute_unary_api_cli_command


def sync_get_external_partition(repository_handle, partition_set_name, partition_name):
    from dagster.cli.api import PartitionApiCommandArgs

    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    repository_origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            repository_origin.executable_path,
            'partition',
            PartitionApiCommandArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_name=partition_name,
            ),
        ),
        ExternalPartitionData,
    )
