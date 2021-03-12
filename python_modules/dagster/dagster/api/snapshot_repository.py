from dagster import check
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_streaming_external_repositories_data_grpc(api_client, repository_location_handle):
    from dagster.core.host_representation import (
        RepositoryLocationHandle,
        ExternalRepositoryOrigin,
    )

    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle
    )

    repo_datas = {}
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

        repo_datas[repository_name] = external_repository_data
    return repo_datas
