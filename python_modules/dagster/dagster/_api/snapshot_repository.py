from collections.abc import Mapping
from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.external_data import RepositoryErrorSnap, RepositorySnap
from dagster._serdes import deserialize_value
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external_data import JobDataSnap
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", code_location: "CodeLocation", defer_snapshots: bool
) -> Mapping[str, tuple[RepositorySnap, Mapping[str, "JobDataSnap"]]]:
    from dagster._core.remote_origin import RemoteRepositoryOrigin
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external_data import (
        extract_serialized_job_snap_from_serialized_job_data_snap,
    )

    check.inst_param(code_location, "code_location", CodeLocation)

    repo_datas = {}
    for repository_name in code_location.repository_names:  # type: ignore
        repo_origin = RemoteRepositoryOrigin(
            code_location.origin,
            repository_name,
        )
        result = deserialize_value(
            api_client.external_repository(
                remote_repository_origin=RemoteRepositoryOrigin(
                    code_location.origin,
                    repository_name,
                ),
                defer_snapshots=defer_snapshots,
            ),
            (RepositorySnap, RepositoryErrorSnap),
        )

        if isinstance(result, RepositoryErrorSnap):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        job_data_snaps = {}

        if not result.has_job_data():
            for job_ref in result.get_job_refs():
                job_response = api_client.external_job(
                    repo_origin,
                    job_ref.name,
                )
                if not job_response.serialized_job_data:
                    error = (
                        deserialize_value(job_response.serialized_error, SerializableErrorInfo)
                        if job_response.serialized_error
                        else "no captured error"
                    )
                    raise Exception(
                        f"Error fetching job data for {job_ref.name} in code server:\n{error}"
                    )
                job_data_snaps[job_ref.name] = (
                    extract_serialized_job_snap_from_serialized_job_data_snap(
                        job_response.serialized_job_data
                    )
                )

        repo_datas[repository_name] = result, job_data_snaps
    return repo_datas
