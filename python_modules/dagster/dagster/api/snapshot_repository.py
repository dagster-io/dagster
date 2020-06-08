from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryData,
    PythonEnvRepositoryLocationHandle,
    RepositoryHandle,
)
from dagster.serdes.ipc import read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_get_external_repositories(repository_location_handle):
    check.inst_param(
        repository_location_handle, 'repository_location_handle', PythonEnvRepositoryLocationHandle,
    )

    repos = []

    for key, pointer in repository_location_handle.repository_code_pointer_dict.items():
        with get_temp_file_name() as output_file:

            parts = [
                repository_location_handle.executable_path,
                '-m',
                'dagster',
                'api',
                'snapshot',
                'repository',
                output_file,
            ] + xplat_shlex_split(pointer.get_cli_args())

            execute_command_in_subprocess(parts)

            external_repository_data = read_unary_response(output_file)
            check.inst(external_repository_data, ExternalRepositoryData)

            repository_handle = RepositoryHandle(
                repository_name=external_repository_data.name,
                repository_key=key,
                repository_location_handle=repository_location_handle,
            )

            repos.append(ExternalRepository(external_repository_data, repository_handle))

    return repos
