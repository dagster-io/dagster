"""This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
"""

from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.host_representation import ExternalJob, ExternalRepository
from dagster._core.host_representation.external_data import (
    external_job_data_from_def,
    external_repository_data_from_def,
)
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryDefinition
    from dagster._core.host_representation.handle import RepositoryHandle


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


def external_repo_from_def(
    repository_def: "RepositoryDefinition", repository_handle: "RepositoryHandle"
) -> ExternalRepository:
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def external_job_from_recon_job(recon_job, op_selection, repository_handle, asset_selection=None):
    if op_selection or asset_selection:
        sub_recon_job = recon_job.get_subset(
            op_selection=op_selection, asset_selection=asset_selection
        )
        job_def = sub_recon_job.get_definition()
    else:
        job_def = recon_job.get_definition()

    return ExternalJob(
        external_job_data_from_def(job_def),
        repository_handle=repository_handle,
    )
