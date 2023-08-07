import sys
from typing import TYPE_CHECKING, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._config import validate_config_from_snap
from dagster._core.definitions.selector import JobSubsetSelector, RepositorySelector
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation import ExternalJob
from dagster._core.host_representation.external import ExternalExecutionPlan
from dagster._core.workspace.context import BaseWorkspaceRequestContext, WorkspaceRequestContext
from dagster._utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError

if TYPE_CHECKING:
    from dagster_graphql.schema.errors import GrapheneRepositoryNotFoundError
    from dagster_graphql.schema.external import (
        GrapheneRepository,
        GrapheneRepositoryConnection,
        GrapheneWorkspace,
        GrapheneWorkspaceLocationStatusEntries,
    )
    from dagster_graphql.schema.util import ResolveInfo


def get_full_external_job_or_raise(
    graphene_info: "ResolveInfo",
    selector: JobSubsetSelector,
) -> ExternalJob:
    check.inst_param(selector, "selector", JobSubsetSelector)
    return _get_external_job_or_raise(graphene_info, selector, ignore_subset=True)


def get_external_job_or_raise(
    graphene_info: "ResolveInfo", selector: JobSubsetSelector
) -> ExternalJob:
    check.inst_param(selector, "selector", JobSubsetSelector)
    return _get_external_job_or_raise(graphene_info, selector)


def _get_external_job_or_raise(
    graphene_info: "ResolveInfo", selector: JobSubsetSelector, ignore_subset: bool = False
) -> ExternalJob:
    from ..schema.errors import GrapheneInvalidSubsetError, GraphenePipelineNotFoundError
    from ..schema.pipelines.pipeline import GraphenePipeline

    ctx = graphene_info.context
    if not ctx.has_external_job(selector):
        raise UserFacingGraphQLError(GraphenePipelineNotFoundError(selector=selector))
    elif ignore_subset:
        external_job = ctx.get_full_external_job(selector)
    else:
        code_location = ctx.get_code_location(selector.location_name)
        try:
            external_job = code_location.get_external_job(selector)
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            raise UserFacingGraphQLError(
                GrapheneInvalidSubsetError(
                    message="{message}{cause_message}".format(
                        message=error_info.message,
                        cause_message=f"\n{error_info.cause.message}" if error_info.cause else "",
                    ),
                    pipeline=GraphenePipeline(ctx.get_full_external_job(selector)),
                )
            )

    return external_job


def ensure_valid_config(external_job: ExternalJob, run_config: object) -> object:
    from ..schema.pipelines.config import GrapheneRunConfigValidationInvalid

    check.inst_param(external_job, "external_job", ExternalJob)
    # do not type check run_config so that validate_config_from_snap throws

    validated_config = validate_config_from_snap(
        config_schema_snapshot=external_job.config_schema_snapshot,
        config_type_key=check.not_none(external_job.root_config_key),
        config_value=run_config,
    )

    if not validated_config.success:
        raise UserFacingGraphQLError(
            GrapheneRunConfigValidationInvalid.for_validation_errors(
                external_job, validated_config.errors
            )
        )

    return validated_config


def get_external_execution_plan_or_raise(
    graphene_info: "ResolveInfo",
    external_pipeline: ExternalJob,
    run_config: Mapping[str, object],
    step_keys_to_execute: Optional[Sequence[str]],
    known_state: Optional[KnownExecutionState],
) -> ExternalExecutionPlan:
    return graphene_info.context.get_external_execution_plan(
        external_job=external_pipeline,
        run_config=run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )


def fetch_repositories(graphene_info: "ResolveInfo") -> "GrapheneRepositoryConnection":
    from ..schema.external import GrapheneRepository, GrapheneRepositoryConnection

    return GrapheneRepositoryConnection(
        nodes=[
            GrapheneRepository(
                instance=graphene_info.context.instance,
                repository=repository,
                repository_location=location,
            )
            for location in graphene_info.context.code_locations
            for repository in location.get_repositories().values()
        ]
    )


def fetch_repository(
    graphene_info: "ResolveInfo", repository_selector: RepositorySelector
) -> Union["GrapheneRepository", "GrapheneRepositoryNotFoundError"]:
    from ..schema.errors import GrapheneRepositoryNotFoundError
    from ..schema.external import GrapheneRepository

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    if graphene_info.context.has_code_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_code_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            return GrapheneRepository(
                instance=graphene_info.context.instance,
                repository=repo_loc.get_repository(repository_selector.repository_name),
                repository_location=repo_loc,
            )

    return GrapheneRepositoryNotFoundError(
        repository_selector.location_name, repository_selector.repository_name
    )


def fetch_workspace(workspace_request_context: WorkspaceRequestContext) -> "GrapheneWorkspace":
    from ..schema.external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry

    check.inst_param(
        workspace_request_context, "workspace_request_context", BaseWorkspaceRequestContext
    )

    nodes = [
        GrapheneWorkspaceLocationEntry(entry)
        for entry in workspace_request_context.get_workspace_snapshot().values()
    ]

    return GrapheneWorkspace(locationEntries=nodes)


def fetch_location_statuses(
    workspace_request_context: WorkspaceRequestContext,
) -> "GrapheneWorkspaceLocationStatusEntries":
    from ..schema.external import (
        GrapheneRepositoryLocationLoadStatus,
        GrapheneWorkspaceLocationStatusEntries,
        GrapheneWorkspaceLocationStatusEntry,
    )

    check.inst_param(
        workspace_request_context, "workspace_request_context", BaseWorkspaceRequestContext
    )

    # passes the ID to the GrapheneWorkspaceLocationStatusEntry, so it can be overridden in Cloud
    return GrapheneWorkspaceLocationStatusEntries(
        entries=[
            GrapheneWorkspaceLocationStatusEntry(
                id=f"location_status:{status_entry.location_name}",
                name=status_entry.location_name,
                load_status=GrapheneRepositoryLocationLoadStatus.from_python_status(
                    status_entry.load_status
                ),
                update_timestamp=status_entry.update_timestamp,
            )
            for status_entry in workspace_request_context.get_code_location_statuses()
        ]
    )
