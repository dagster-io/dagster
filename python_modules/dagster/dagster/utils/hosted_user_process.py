'''
This file contains a set of utilities for dealing with test
environments where we want to go back and forth between
abstractions that reside in user process (e.g. definitions and
reconstructables) and abstractions that reside in host processes
(e.g. handles and externals).

These should only be invoked from contexts where we know this
to be the case.
'''

from dagster import check
from dagster.core.definitions.reconstructable import (
    ReconstructableRepository,
    repository_def_from_pointer,
)
from dagster.core.host_representation import ExternalPipeline, ExternalRepository, PipelineHandle
from dagster.core.host_representation.external_data import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)


# we can do this because we only use in a hosted user process
def pipeline_def_from_pipeline_handle(pipeline_handle):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    pointer = pipeline_handle.repository_handle.get_pointer()
    repo_def = repository_def_from_pointer(pointer)
    return repo_def.get_pipeline(pipeline_handle.pipeline_name)


def recon_pipeline_from_pipeline_handle(pipeline_handle):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    pointer = pipeline_handle.repository_handle.get_pointer()
    recon_repo = ReconstructableRepository(pointer)
    return recon_repo.get_reconstructable_pipeline(pipeline_handle.pipeline_name)


def external_repo_from_def(repository_def, repository_handle):
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def external_pipeline_from_recon_pipeline(recon_pipeline, solid_subset, repository_handle):
    full_pipeline_def = recon_pipeline.get_definition()

    pipeline_def = (
        full_pipeline_def.get_pipeline_subset_def(solid_subset)
        if solid_subset
        else full_pipeline_def
    )

    return ExternalPipeline(
        external_pipeline_data_from_def(pipeline_def), repository_handle=repository_handle,
    )
