from collections.abc import Mapping
from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.external_data import RepositoryErrorSnap, RepositorySnap
from dagster._serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", code_location: "CodeLocation"
) -> Mapping[str, RepositorySnap]:
    from dagster._core.remote_origin import RemoteRepositoryOrigin
    from dagster._core.remote_representation.code_location import CodeLocation

    check.inst_param(code_location, "code_location", CodeLocation)

    repo_datas = {}
    for repository_name in code_location.repository_names:  # type: ignore
        result = deserialize_value(
            api_client.external_repository(
                remote_repository_origin=RemoteRepositoryOrigin(
                    code_location.origin,
                    repository_name,
                )
            ),
            (RepositorySnap, RepositoryErrorSnap),
        )

        if isinstance(result, RepositoryErrorSnap):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        repo_datas[repository_name] = result
    return repo_datas


async def gen_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", code_location: "CodeLocation"
) -> Mapping[str, RepositorySnap]:
    from dagster._core.remote_origin import RemoteRepositoryOrigin
    from dagster._core.remote_representation.code_location import CodeLocation

    check.inst_param(code_location, "code_location", CodeLocation)

    repo_datas = {}
    for repository_name in code_location.repository_names:  # type: ignore
        result = deserialize_value(
            await api_client.gen_external_repository(
                remote_repository_origin=RemoteRepositoryOrigin(
                    code_location.origin,
                    repository_name,
                )
            ),
            (RepositorySnap, RepositoryErrorSnap),
        )

        if isinstance(result, RepositoryErrorSnap):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        repo_datas[repository_name] = result
    return repo_datas
