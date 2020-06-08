from dagster import check
from dagster.core.host_representation.external_data import ExternalPartitionData
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_partition(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')

    pointer = repository_handle.get_pointer()
    location_handle = repository_handle.repository_location_handle

    with get_temp_file_name() as output_file:
        parts = (
            [
                location_handle.executable_path,
                '-m',
                'dagster',
                'api',
                'snapshot',
                'partition',
                output_file,
            ]
            + xplat_shlex_split(pointer.get_cli_args())
            + [
                '--partition-set-name={}'.format(partition_set_name),
                '--partition-name={}'.format(partition_name),
            ]
        )
        execute_command_in_subprocess(parts)
        partition_snapshot = read_unary_response(output_file)
        check.inst(partition_snapshot, ExternalPartitionData)
        return partition_snapshot
