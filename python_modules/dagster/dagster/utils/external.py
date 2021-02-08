import contextlib

from dagster import check
from dagster.core.host_representation import (
    ExternalPipeline,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.host_representation.origin import ExternalPipelineOrigin
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.storage.pipeline_run import PipelineRun


@contextlib.contextmanager
def repository_location_handle_from_run(pipeline_run):
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

    external_pipeline_origin = check.inst(
        pipeline_run.external_pipeline_origin, ExternalPipelineOrigin
    )
    origin = external_pipeline_origin.external_repository_origin.repository_location_origin
    with origin.create_handle() as handle:
        yield handle


def external_pipeline_from_location_handle(
    repository_location_handle, external_pipeline_origin, solid_selection
):
    check.inst_param(
        repository_location_handle, "repository_location_handle", RepositoryLocationHandle
    )
    check.inst_param(external_pipeline_origin, "external_pipeline_origin", ExternalPipelineOrigin)

    repo_location = RepositoryLocation.from_handle(repository_location_handle)
    repo_name = external_pipeline_origin.external_repository_origin.repository_name
    pipeline_name = external_pipeline_origin.pipeline_name

    check.invariant(
        repo_location.has_repository(repo_name),
        "Could not find repository {repo_name} in location {repo_location_name}".format(
            repo_name=repo_name, repo_location_name=repo_location.name
        ),
    )
    external_repo = repo_location.get_repository(repo_name)

    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=pipeline_name,
        solid_selection=solid_selection,
    )

    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    external_pipeline = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data,
        external_repo.handle,
    )
    return external_pipeline


@contextlib.contextmanager
def external_pipeline_from_run(pipeline_run):
    with repository_location_handle_from_run(pipeline_run) as repo_location_handle:
        yield external_pipeline_from_location_handle(
            repo_location_handle,
            pipeline_run.external_pipeline_origin,
            pipeline_run.solid_selection,
        )
