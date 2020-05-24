import subprocess

from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryData,
    RepositoryHandle,
)
from dagster.serdes.ipc import ipc_read_event_stream
from dagster.utils.temp_file import get_temp_file_name


def sync_get_external_repository(repo_handle):
    check.inst_param(repo_handle, 'repo_handle', RepositoryHandle)

    with get_temp_file_name() as output_file:

        parts = [
            'dagster',
            'api',
            'snapshot',
            'repository',
            output_file,
            '-y',
            repo_handle.environment_handle.in_process_origin.repo_yaml,
        ]

        process = subprocess.Popen(parts)

        _stdout, _stderr = process.communicate()

        check.invariant(
            process.returncode == 0, 'dagster api cli invocation did not complete successfully'
        )

        messages = list(ipc_read_event_stream(output_file))
        check.invariant(len(messages) == 1)

        external_repository_data = messages[0]

        check.inst(external_repository_data, ExternalRepositoryData)

        return ExternalRepository(external_repository_data, repo_handle)
