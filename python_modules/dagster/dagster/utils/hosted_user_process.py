"""
This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
"""

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import ExternalPipeline, ExternalRepository
from dagster.core.host_representation.external_data import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin


def recon_pipeline_from_origin(origin):
    check.inst_param(origin, "origin", PipelinePythonOrigin)
    recon_repo = ReconstructableRepository(origin.get_repo_pointer())
    return recon_repo.get_reconstructable_pipeline(origin.pipeline_name)


def recon_repository_from_origin(origin):
    check.inst_param(origin, "origin", RepositoryPythonOrigin)
    return ReconstructableRepository(origin.code_pointer)


def external_repo_from_def(repository_def, repository_handle):
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def recon_repo_from_external_repo(external_repo):
    return ReconstructableRepository(external_repo.get_python_origin().code_pointer)


def external_pipeline_from_recon_pipeline(recon_pipeline, solid_selection, repository_handle):
    if solid_selection:
        sub_pipeline = recon_pipeline.subset_for_execution(solid_selection)
        pipeline_def = sub_pipeline.get_definition()
    else:
        pipeline_def = recon_pipeline.get_definition()

    return ExternalPipeline(
        external_pipeline_data_from_def(pipeline_def),
        repository_handle=repository_handle,
    )
