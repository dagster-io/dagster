from typing import TYPE_CHECKING, Mapping

import dagster._check as check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import (
    ExternalRepositoryData,
    ExternalRepositoryErrorData,
)
from dagster.serdes import deserialize_as

if TYPE_CHECKING:
    from dagster.core.host_representation import RepositoryLocation
    from dagster.grpc.client import DagsterGrpcClient


def sync_get_streaming_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", repository_location: "RepositoryLocation"
) -> Mapping[str, ExternalRepositoryData]:
    from dagster.core.host_representation import ExternalRepositoryOrigin, RepositoryLocation

    check.inst_param(repository_location, "repository_location", RepositoryLocation)

    repo_datas = {}
    for repository_name in repository_location.repository_names:  # type: ignore
        external_repository_chunks = list(
            api_client.streaming_external_repository(
                external_repository_origin=ExternalRepositoryOrigin(
                    repository_location.origin,
                    repository_name,
                )
            )
        )

        result = deserialize_as(
            "".join(
                [
                    chunk["serialized_external_repository_chunk"]
                    for chunk in external_repository_chunks
                ]
            ),
            (ExternalRepositoryData, ExternalRepositoryErrorData),
        )

        if isinstance(result, ExternalRepositoryErrorData):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        repo_datas[repository_name] = result
    return repo_datas
