from dagster import check
from dagster.serdes.ipc import read_unary_response
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_list_repositories(executable_path, python_file, module_name):
    from dagster.cli.api import ListRepositoriesResponse

    with get_temp_file_name() as output_file:
        parts = [
            executable_path,
            '-m',
            'dagster',
            'api',
            'snapshot',
            'list_repositories',
            output_file,
        ] + (['-f', python_file] if python_file else ['--module-name', module_name])

        execute_command_in_subprocess(parts)

        response = read_unary_response(output_file)

        return check.inst(response, ListRepositoriesResponse)
