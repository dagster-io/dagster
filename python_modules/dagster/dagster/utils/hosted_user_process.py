"""
This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
"""

from typing import TYPE_CHECKING

import dagster._check as check
from dagster.core.definitions.reconstruct import ReconstructablePipeline, ReconstructableRepository
from dagster.core.host_representation import ExternalPipeline, ExternalRepository
from dagster.core.host_representation.external_data import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin

if TYPE_CHECKING:
    from dagster.core.definitions.repository_definition import RepositoryDefinition
    from dagster.core.host_representation.handle import RepositoryHandle


def recon_pipeline_from_origin(origin: PipelinePythonOrigin) -> ReconstructablePipeline:
    check.inst_param(origin, "origin", PipelinePythonOrigin)
    recon_repo = recon_repository_from_origin(origin.repository_origin)
    return recon_repo.get_reconstructable_pipeline(origin.pipeline_name)


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
):
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def external_pipeline_from_recon_pipeline(
    recon_pipeline, solid_selection, repository_handle, asset_selection=None
):
    if solid_selection or asset_selection:
        sub_pipeline = recon_pipeline.subset_for_execution(
            solid_selection=solid_selection, asset_selection=asset_selection
        )
        pipeline_def = sub_pipeline.get_definition()
    else:
        pipeline_def = recon_pipeline.get_definition()

    return ExternalPipeline(
        external_pipeline_data_from_def(pipeline_def),
        repository_handle=repository_handle,
    )
