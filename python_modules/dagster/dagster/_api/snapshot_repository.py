from typing import TYPE_CHECKING, Mapping

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.host_representation.external_data import (
    ExternalRepositoryData,
    ExternalRepositoryErrorData,
)
from dagster._serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._core.host_representation import CodeLocation
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_streaming_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", code_location: "CodeLocation"
) -> Mapping[str, ExternalRepositoryData]:
    from dagster._core.host_representation import CodeLocation, ExternalRepositoryOrigin

    check.inst_param(code_location, "code_location", CodeLocation)

    repo_datas = {}
    for repository_name in code_location.repository_names:  # type: ignore
        external_repository_chunks = list(
            api_client.streaming_external_repository(
                external_repository_origin=ExternalRepositoryOrigin(
                    code_location.origin,
                    repository_name,
                )
            )
        )

        result = deserialize_value(
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
