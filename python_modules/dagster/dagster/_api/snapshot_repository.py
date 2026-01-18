import os
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.external_data import RepositoryErrorSnap, RepositorySnap
from dagster._serdes import deserialize_value
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.snap import JobSnap
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_repositories_data_grpc(
    api_client: "DagsterGrpcClient", code_location: "CodeLocation", defer_snapshots: bool
) -> Mapping[str, tuple[RepositorySnap, Mapping[str, "JobSnap"]]]:
    from dagster._core.remote_origin import RemoteRepositoryOrigin
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external_data import (
        extract_serialized_job_snap_from_serialized_job_data_snap,
    )
    from dagster._core.snap import JobSnap

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

        job_snaps = {}

        if not result.has_job_data():
            job_refs = result.get_job_refs()
            with ThreadPoolExecutor(
                max_workers=int(os.getenv("DAGSTER_EXTERNAL_JOB_THREADPOOL_WORKERS", "4"))
            ) as executor:
                job_responses = list(
                    executor.map(
                        lambda job_ref: api_client.external_job(
                            repo_origin,
                            job_ref.name,
                        ),
                        job_refs,
                    )
                )

            for i, job_ref in enumerate(job_refs):
                job_response = job_responses[i]
                if not job_response.serialized_job_data:
                    error = (
                        deserialize_value(job_response.serialized_error, SerializableErrorInfo)
                        if job_response.serialized_error
                        else "no captured error"
                    )
                    raise Exception(
                        f"Error fetching job data for {job_ref.name} in code server:\n{error}"
                    )
                job_snap = deserialize_value(
                    extract_serialized_job_snap_from_serialized_job_data_snap(
                        job_response.serialized_job_data
                    ),
                    JobSnap,
                )

                job_snaps[job_ref.name] = job_snap

        repo_datas[repository_name] = result, job_snaps
    return repo_datas
