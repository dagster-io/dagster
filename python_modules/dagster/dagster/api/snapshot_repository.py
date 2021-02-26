from dagster import check
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryData,
    ExternalRepositoryOrigin,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_external_repositories_grpc(api_client, repository_location_handle):
    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle
    )

    repos = []
    for repository_name in repository_location_handle.repository_names:
        external_repository_data = check.inst(
            api_client.external_repository(
                external_repository_origin=ExternalRepositoryOrigin(
                    repository_location_handle.origin,
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
                external_repository_origin=ExternalRepositoryOrigin(
                    repository_location_handle.origin,
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
