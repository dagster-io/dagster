from dagster import check

from .utils import execute_unary_api_cli_command


def sync_list_repositories(executable_path, python_file, module_name, working_directory):
    from dagster.grpc.types import ListRepositoriesResponse, ListRepositoriesInput

    return check.inst(
        execute_unary_api_cli_command(
            executable_path,
            'list_repositories',
            ListRepositoriesInput(
                module_name=module_name,
                python_file=python_file,
                working_directory=working_directory,
            ),
        ),
        ListRepositoriesResponse,
    )


def sync_list_repositories_grpc(executable_path, python_file, module_name, working_directory):
    from dagster.grpc.client import ephemeral_grpc_api_client
    from dagster.grpc.types import ListRepositoriesArgs, ListRepositoriesResponse

    check.str_param(executable_path, 'executable_path')
    check.opt_str_param(python_file, 'python_file')
    check.opt_str_param(module_name, 'module_name')
    check.opt_str_param(working_directory, 'working_directory')

    with ephemeral_grpc_api_client(python_executable_path=executable_path) as api_client:
        return check.inst(
            api_client.list_repositories(
                ListRepositoriesArgs(
                    module_name=module_name,
                    python_file=python_file,
                    working_directory=working_directory,
                )
            ),
            ListRepositoriesResponse,
        )
