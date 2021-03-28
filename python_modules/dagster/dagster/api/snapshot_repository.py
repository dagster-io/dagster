from dagster import check
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_streaming_external_repositories_data_grpc(api_client, repository_location):
    from dagster.core.host_representation import (
        RepositoryLocation,
        ExternalRepositoryOrigin,
    )

    check.inst_param(repository_location, "repository_location", RepositoryLocation)

    repo_datas = {}
    for repository_name in repository_location.repository_names:
        external_repository_chunks = list(
            api_client.streaming_external_repository(
                external_repository_origin=ExternalRepositoryOrigin(
                    repository_location.origin,
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
