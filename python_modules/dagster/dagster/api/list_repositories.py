from dagster import check
from dagster.serdes.ipc import read_unary_response, write_unary_input
from dagster.utils.temp_file import get_temp_file_name

from .utils import execute_command_in_subprocess


def sync_list_repositories(executable_path, python_file, module_name):
    from dagster.cli.api import ListRepositoriesResponse, ListRepositoriesInput

    with get_temp_file_name() as input_file, get_temp_file_name() as output_file:
        parts = [
            executable_path,
            '-m',
            'dagster',
            'api',
            'snapshot',
            'list_repositories',
            input_file,
            output_file,
        ]

        write_unary_input(
            input_file, ListRepositoriesInput(module_name=module_name, python_file=python_file)
        )

        execute_command_in_subprocess(parts)

        response = read_unary_response(output_file)

        return check.inst(response, ListRepositoriesResponse)
