from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._config import validate_config_from_snap
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation import ExternalPipeline, PipelineSelector, RepositorySelector
from dagster._core.host_representation.external import ExternalExecutionPlan
from dagster._core.workspace.context import BaseWorkspaceRequestContext, WorkspaceRequestContext
from dagster._utils.error import serializable_error_info_from_exc_info
from graphene import ResolveInfo

from .utils import UserFacingGraphQLError, capture_error

if TYPE_CHECKING:
    from dagster_graphql.schema.errors import GrapheneRepositoryNotFoundError
    from dagster_graphql.schema.external import (
        GrapheneRepository,
        GrapheneRepositoryConnection,
        GrapheneWorkspace,
        GrapheneWorkspaceLocationStatusEntries,
    )
    from dagster_graphql.schema.util import HasContext


def get_full_external_pipeline_or_raise(
    graphene_info: "HasContext",
    selector: PipelineSelector,
) -> ExternalPipeline:
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    return _get_external_pipeline_or_raise(graphene_info, selector, ignore_subset=True)


def get_external_pipeline_or_raise(
    graphene_info: "HasContext", selector: PipelineSelector
) -> ExternalPipeline:
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    return _get_external_pipeline_or_raise(graphene_info, selector)


def _get_external_pipeline_or_raise(
    graphene_info: "HasContext", selector: PipelineSelector, ignore_subset: bool = False
) -> ExternalPipeline:
    from ..schema.errors import GrapheneInvalidSubsetError, GraphenePipelineNotFoundError
    from ..schema.pipelines.pipeline import GraphenePipeline

    ctx = graphene_info.context
    if not ctx.has_external_job(selector):
        raise UserFacingGraphQLError(GraphenePipelineNotFoundError(selector=selector))
    elif ignore_subset:
        external_pipeline = ctx.get_full_external_job(selector)
    else:
        repository_location = ctx.get_repository_location(selector.location_name)
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
                    pipeline=GraphenePipeline(ctx.get_full_external_job(selector)),
                )
            )

    return external_pipeline


def ensure_valid_config(
    external_pipeline: ExternalPipeline, mode: Optional[str], run_config: object
) -> object:
    from ..schema.pipelines.config import GrapheneRunConfigValidationInvalid

    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.opt_str_param(mode, "mode")
    # do not type check run_config so that validate_config_from_snap throws

    validated_config = validate_config_from_snap(
        config_schema_snapshot=external_pipeline.config_schema_snapshot,
        config_type_key=check.not_none(external_pipeline.root_config_key_for_mode(mode)),
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
    graphene_info: "HasContext",
    external_pipeline: ExternalPipeline,
    mode: Optional[str],
    run_config: Mapping[str, object],
    step_keys_to_execute: Optional[Sequence[str]],
    known_state: Optional[KnownExecutionState],
) -> ExternalExecutionPlan:
    return graphene_info.context.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=check.not_none(mode),
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )


@capture_error
def fetch_repositories(graphene_info: "HasContext") -> GrapheneRepositoryConnection:
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
def fetch_repository(
    graphene_info: "HasContext", repository_selector: RepositorySelector
) -> Union[GrapheneRepository, GrapheneRepositoryNotFoundError]:
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
def fetch_workspace(workspace_request_context: WorkspaceRequestContext) -> GrapheneWorkspace:
    from ..schema.external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry

    check.inst_param(
        workspace_request_context, "workspace_request_context", BaseWorkspaceRequestContext
    )

    nodes = [
        GrapheneWorkspaceLocationEntry(entry)
        for entry in workspace_request_context.get_workspace_snapshot().values()
    ]

    return GrapheneWorkspace(locationEntries=nodes)


@capture_error
def fetch_location_statuses(
    workspace_request_context: WorkspaceRequestContext,
) -> GrapheneWorkspaceLocationStatusEntries:
    from ..schema.external import (
        GrapheneRepositoryLocationLoadStatus,
        GrapheneWorkspaceLocationStatusEntries,
        GrapheneWorkspaceLocationStatusEntry,
    )

    check.inst_param(
        workspace_request_context, "workspace_request_context", BaseWorkspaceRequestContext
    )
    return GrapheneWorkspaceLocationStatusEntries(
        entries=[
            GrapheneWorkspaceLocationStatusEntry(
                name=status_entry.location_name,
                load_status=GrapheneRepositoryLocationLoadStatus.from_python_status(
                    status_entry.load_status
                ),
                update_timestamp=status_entry.update_timestamp,
            )
            for status_entry in workspace_request_context.get_location_statuses()
        ]
    )
