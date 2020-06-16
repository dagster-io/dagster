from dagster import check

from .utils import execute_unary_api_cli_command


def sync_list_repositories(executable_path, python_file, module_name):
    from dagster.cli.api import ListRepositoriesResponse, ListRepositoriesInput

    return check.inst(
        execute_unary_api_cli_command(
            executable_path,
            'list_repositories',
            ListRepositoriesInput(module_name=module_name, python_file=python_file),
        ),
        ListRepositoriesResponse,
    )
