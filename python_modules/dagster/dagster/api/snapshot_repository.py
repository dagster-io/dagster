from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryData,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from dagster.core.origin import RepositoryGrpcServerOrigin, RepositoryPythonOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple

from .utils import execute_unary_api_cli_command


def sync_get_external_repositories(repository_location_handle):
    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle,
    )

    repos = []

    for _, pointer in repository_location_handle.repository_code_pointer_dict.items():
        external_repository_data = check.inst(
            execute_unary_api_cli_command(
                repository_location_handle.executable_path,
                "repository",
                RepositoryPythonOrigin(repository_location_handle.executable_path, pointer),
            ),
            ExternalRepositoryData,
        )
        repos.append(
            ExternalRepository(
                external_repository_data,
                RepositoryHandle(
                    repository_name=external_repository_data.name,
                    repository_location_handle=repository_location_handle,
                ),
            )
        )

    return repos


def sync_get_external_repositories_grpc(api_client, repository_location_handle):
    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle
    )

    repos = []
    for repository_name in repository_location_handle.repository_names:
        external_repository_data = check.inst(
            api_client.external_repository(
                repository_grpc_server_origin=RepositoryGrpcServerOrigin(
                    repository_location_handle.host,
                    repository_location_handle.port,
                    repository_location_handle.socket,
                    repository_name,
                )
            ),
            ExternalRepositoryData,
        )
        repos.append(
            ExternalRepository(
                external_repository_data,
                RepositoryHandle(
                    repository_name=external_repository_data.name,
                    repository_location_handle=repository_location_handle,
                ),
            )
        )
    return repos


def sync_get_streaming_external_repositories_grpc(api_client, repository_location_handle):
    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle
    )

    repos = []
    for repository_name in repository_location_handle.repository_names:
        external_repository_chunks = list(
            api_client.streaming_external_repository(
                repository_grpc_server_origin=RepositoryGrpcServerOrigin(
                    repository_location_handle.host,
                    repository_location_handle.port,
                    repository_location_handle.socket,
                    repository_name,
                )
            )
        )

        external_repository_data = deserialize_json_to_dagster_namedtuple(
            "".join(
                [
                    chunk["serialized_external_repository_chunk"]
                    for chunk in external_repository_chunks
                ]
            )
        )

        repos.append(
            ExternalRepository(
                external_repository_data,
                RepositoryHandle(
                    repository_name=external_repository_data.name,
                    repository_location_handle=repository_location_handle,
                ),
            )
        )
    return repos
