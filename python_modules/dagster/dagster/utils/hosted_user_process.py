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
from dagster.core.host_representation import (
    EnvironmentHandle,
    ExternalPipeline,
    ExternalRepository,
    InProcessOrigin,
    PipelineHandle,
    RepositoryHandle,
)
from dagster.core.host_representation.external_data import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.core.host_representation.pipeline_index import PipelineIndex
from dagster.core.snap import PipelineSnapshot


# we can do this because we only use in a hosted user process
def pipeline_def_from_pipeline_handle(pipeline_handle):
    check.inst_param(pipeline_handle, 'pipeline_handle', PipelineHandle)
    pointer = pipeline_handle.repository_handle.environment_handle.in_process_origin.pointer
    repo_def = repository_def_from_pointer(pointer)
    return repo_def.get_pipeline(pipeline_handle.pipeline_name)


def repository_handle_from_recon_repo(recon_repo):
    check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
    repository_name = recon_repo.get_definition().name
    return RepositoryHandle(
        repository_name=repository_name,
        environment_handle=EnvironmentHandle(
            environment_name=repository_name + '-environment',
            in_process_origin=InProcessOrigin(
                pointer=recon_repo.pointer, repo_yaml=recon_repo.yaml_path
            ),
        ),
    )


def repository_handle_from_yaml(yaml_path):
    check.str_param(yaml_path, 'yaml_path')
    return repository_handle_from_recon_repo(ReconstructableRepository.from_yaml(yaml_path))


def external_repo_from_recon_repo(recon_repo):
    check.inst_param(recon_repo, 'recon_repo', ReconstructableRepository)
    return external_repo_from_def(
        recon_repo.get_definition(), repository_handle_from_recon_repo(recon_repo)
    )


def external_repo_from_def(repository_def, repository_handle):
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle,)


def external_repo_from_yaml(yaml_path):
    check.str_param(yaml_path, 'yaml_path')
    return external_repo_from_recon_repo(ReconstructableRepository.from_yaml(yaml_path))


def external_repo_from_repository_handle(repository_handle):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)

    pointer = repository_handle.environment_handle.in_process_origin.pointer
    repository_def = repository_def_from_pointer(pointer)
    return ExternalRepository(external_repository_data_from_def(repository_def), repository_handle)


def external_pipeline_from_recon_pipeline(recon_pipeline, solid_subset):
    full_pipeline_def = recon_pipeline.get_definition()
    repository_handle = repository_handle_from_recon_repo(recon_pipeline.repository)

    pipeline_def = (
        full_pipeline_def.subset_for_execution(solid_subset) if solid_subset else full_pipeline_def
    )

    return ExternalPipeline(
        PipelineIndex(PipelineSnapshot.from_pipeline_def(pipeline_def)),
        external_pipeline_data_from_def(pipeline_def),
        solid_subset=solid_subset,
        repository_handle=repository_handle,
    )
