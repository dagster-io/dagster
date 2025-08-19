"""This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
"""

from collections.abc import Iterable
from typing import AbstractSet, Optional  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.remote_representation.external_data import JobDataSnap
from dagster._core.remote_representation.handle import RepositoryHandle


def recon_job_from_origin(origin: JobPythonOrigin) -> ReconstructableJob:
    check.inst_param(origin, "origin", JobPythonOrigin)
    recon_repo = recon_repository_from_origin(origin.repository_origin)
    return recon_repo.get_reconstructable_job(origin.job_name)


def recon_repository_from_origin(origin: RepositoryPythonOrigin) -> "ReconstructableRepository":
    check.inst_param(origin, "origin", RepositoryPythonOrigin)
    return ReconstructableRepository(
        origin.code_pointer,
        origin.container_image,
        origin.executable_path,
        origin.entry_point,
        origin.container_context,
    )


def remote_job_from_recon_job(
    recon_job: ReconstructableJob,
    op_selection: Optional[Iterable[str]],
    repository_handle: RepositoryHandle,
    asset_selection: Optional[AbstractSet[AssetKey]] = None,
) -> RemoteJob:
    if op_selection or asset_selection:
        sub_recon_job = recon_job.get_subset(
            op_selection=op_selection, asset_selection=asset_selection
        )
        job_def = sub_recon_job.get_definition()
    else:
        job_def = recon_job.get_definition()

    return RemoteJob(
        JobDataSnap.from_job_def(job_def, include_parent_snapshot=True),
        repository_handle=repository_handle,
    )
