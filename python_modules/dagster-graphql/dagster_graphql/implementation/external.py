import sys

from graphene import ResolveInfo

import dagster._check as check
from dagster._config import validate_config_from_snap
from dagster._core.host_representation import ExternalPipeline, PipelineSelector, RepositorySelector
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError, capture_error


def get_full_external_job_or_raise(graphene_info, selector):
    from ..schema.errors import GraphenePipelineNotFoundError

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)

    if not graphene_info.context.has_external_job(selector):
        raise UserFacingGraphQLError(GraphenePipelineNotFoundError(selector=selector))

    return graphene_info.context.get_full_external_job(selector)


def get_external_pipeline_or_raise(graphene_info, selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)

    full_pipeline = get_full_external_job_or_raise(graphene_info, selector)

    if selector.solid_selection is None and selector.asset_selection is None:
        return full_pipeline

    return get_subset_external_pipeline(graphene_info.context, selector)


def get_subset_external_pipeline(context, selector):
    from ..schema.errors import GrapheneInvalidSubsetError
    from ..schema.pipelines.pipeline import GraphenePipeline

    check.inst_param(selector, "selector", PipelineSelector)

    repository_location = context.get_repository_location(selector.location_name)

    try:
        external_pipeline = repository_location.get_external_pipeline(selector)
    except Exception:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        raise UserFacingGraphQLError(
            GrapheneInvalidSubsetError(
                message="{message}{cause_message}".format(
                    message=error_info.message,
                    cause_message="\n{}".format(error_info.cause.message)
                    if error_info.cause
                    else "",
                ),
                pipeline=GraphenePipeline(context.get_full_external_job(selector)),
            )
        )

    return external_pipeline


def ensure_valid_config(external_pipeline, mode, run_config):
    from ..schema.pipelines.config import GrapheneRunConfigValidationInvalid

    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.opt_str_param(mode, "mode")
    # do not type check run_config so that validate_config_from_snap throws

    validated_config = validate_config_from_snap(
        config_schema_snapshot=external_pipeline.config_schema_snapshot,
        config_type_key=external_pipeline.root_config_key_for_mode(mode),
        config_value=run_config,
    )

    if not validated_config.success:

        raise UserFacingGraphQLError(
            GrapheneRunConfigValidationInvalid.for_validation_errors(
                external_pipeline, validated_config.errors
            )
        )

    return validated_config


def get_external_execution_plan_or_raise(
    graphene_info,
    external_pipeline,
    mode,
    run_config,
    step_keys_to_execute,
    known_state,
):

    return graphene_info.context.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )


@capture_error
def fetch_repositories(graphene_info):
    from ..schema.external import GrapheneRepository, GrapheneRepositoryConnection

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    return GrapheneRepositoryConnection(
        nodes=[
            GrapheneRepository(
                instance=graphene_info.context.instance,
                repository=repository,
                repository_location=location,
            )
            for location in graphene_info.context.repository_locations
            for repository in location.get_repositories().values()
        ]
    )


@capture_error
def fetch_repository(graphene_info, repository_selector):
    from ..schema.errors import GrapheneRepositoryNotFoundError
    from ..schema.external import GrapheneRepository

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    if graphene_info.context.has_repository_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_repository_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            return GrapheneRepository(
                instance=graphene_info.context.instance,
                repository=repo_loc.get_repository(repository_selector.repository_name),
                repository_location=repo_loc,
            )

    return GrapheneRepositoryNotFoundError(
        repository_selector.location_name, repository_selector.repository_name
    )


@capture_error
def fetch_workspace(workspace_request_context):
    from ..schema.external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry

    check.inst_param(
        workspace_request_context, "workspace_request_context", BaseWorkspaceRequestContext
    )

    nodes = [
        GrapheneWorkspaceLocationEntry(entry)
        for entry in workspace_request_context.get_workspace_snapshot().values()
    ]

    return GrapheneWorkspace(locationEntries=nodes)
