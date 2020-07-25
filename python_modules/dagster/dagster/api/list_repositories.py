from dagster import check

from .utils import execute_unary_api_cli_command


def sync_list_repositories(executable_path, python_file, module_name, working_directory, attribute):
    from dagster.grpc.types import ListRepositoriesResponse, ListRepositoriesInput

    return check.inst(
        execute_unary_api_cli_command(
            executable_path,
            'list_repositories',
            ListRepositoriesInput(
                module_name=module_name,
                python_file=python_file,
                working_directory=working_directory,
                attribute=attribute,
            ),
        ),
        ListRepositoriesResponse,
    )


def sync_list_repositories_grpc(api_client):
    from dagster.grpc.client import DagsterGrpcClient
    from dagster.grpc.types import ListRepositoriesResponse

    check.inst_param(api_client, 'api_client', DagsterGrpcClient)
    return check.inst(api_client.list_repositories(), ListRepositoriesResponse)


def sync_list_repositories_ephemeral_grpc(
    executable_path, python_file, module_name, working_directory, attribute
):
    from dagster.grpc.client import ephemeral_grpc_api_client
    from dagster.grpc.types import LoadableTargetOrigin

    check.str_param(executable_path, 'executable_path')
    check.opt_str_param(python_file, 'python_file')
    check.opt_str_param(module_name, 'module_name')
    check.opt_str_param(working_directory, 'working_directory')

    with ephemeral_grpc_api_client(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=executable_path,
            module_name=module_name,
            python_file=python_file,
            working_directory=working_directory,
            attribute=attribute,
        )
    ) as api_client:
        return sync_list_repositories_grpc(api_client)
