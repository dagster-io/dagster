from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryData,
    LocationHandle,
    RepositoryHandle,
)
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_repository(location_handle):
    check.inst_param(location_handle, 'location_handle', LocationHandle)

    with get_temp_file_name() as output_file:

        parts = ['dagster', 'api', 'snapshot', 'repository', output_file] + xplat_shlex_split(
            location_handle.pointer.get_cli_args()
        )

        execute_command_in_subprocess(parts)

        external_repository_data = read_unary_response(output_file)
        check.inst(external_repository_data, ExternalRepositoryData)

        return ExternalRepository(
            external_repository_data,
            RepositoryHandle(external_repository_data.name, location_handle),
        )
