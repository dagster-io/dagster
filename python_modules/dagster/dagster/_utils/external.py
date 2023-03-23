from typing import Optional, Sequence

import dagster._check as check
from dagster._core.definitions.selector import PipelineSelector
from dagster._core.host_representation import CodeLocation
from dagster._core.host_representation.external import ExternalPipeline
from dagster._core.host_representation.origin import ExternalPipelineOrigin


def external_pipeline_from_location(
    code_location: CodeLocation,
    external_pipeline_origin: ExternalPipelineOrigin,
    solid_selection: Optional[Sequence[str]],
) -> ExternalPipeline:
    check.inst_param(code_location, "code_location", CodeLocation)
    check.inst_param(external_pipeline_origin, "external_pipeline_origin", ExternalPipelineOrigin)

    repo_name = external_pipeline_origin.external_repository_origin.repository_name
    pipeline_name = external_pipeline_origin.pipeline_name

    check.invariant(
        code_location.has_repository(repo_name),
        f"Could not find repository {repo_name} in location {code_location.name}",
    )
    external_repo = code_location.get_repository(repo_name)

    pipeline_selector = PipelineSelector(
        location_name=code_location.name,
        repository_name=external_repo.name,
        pipeline_name=pipeline_name,
        solid_selection=solid_selection,
    )

    return code_location.get_external_pipeline(pipeline_selector)
