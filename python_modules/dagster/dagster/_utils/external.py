from collections.abc import Sequence
from typing import Optional

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.remote_representation import CodeLocation
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.remote_representation.origin import RemoteJobOrigin


def remote_job_from_location(
    code_location: CodeLocation,
    remote_job_origin: RemoteJobOrigin,
    op_selection: Optional[Sequence[str]],
) -> RemoteJob:
    check.inst_param(code_location, "code_location", CodeLocation)
    check.inst_param(remote_job_origin, "external_pipeline_origin", RemoteJobOrigin)

    repo_name = remote_job_origin.repository_origin.repository_name
    job_name = remote_job_origin.job_name

    check.invariant(
        code_location.has_repository(repo_name),
        f"Could not find repository {repo_name} in location {code_location.name}",
    )
    repo = code_location.get_repository(repo_name)

    pipeline_selector = JobSubsetSelector(
        location_name=code_location.name,
        repository_name=repo.name,
        job_name=job_name,
        op_selection=op_selection,
    )

    return code_location.get_job(pipeline_selector)
