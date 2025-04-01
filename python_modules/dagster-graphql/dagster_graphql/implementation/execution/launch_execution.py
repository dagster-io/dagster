from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional, cast

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.execution.run_lifecycle import create_valid_pipeline_run
from dagster_graphql.implementation.external import get_remote_job_or_raise
from dagster_graphql.implementation.utils import (
    ExecutionMetadata,
    ExecutionParams,
    assert_permission_for_location,
)

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

    from dagster_graphql.schema.runs import GrapheneLaunchRunSuccess
    from dagster_graphql.schema.util import ResolveInfo


def launch_pipeline_reexecution(
    graphene_info: "ResolveInfo", execution_params: ExecutionParams
) -> "GrapheneLaunchRunSuccess":
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


def launch_pipeline_execution(
    graphene_info: "ResolveInfo", execution_params: ExecutionParams
) -> "GrapheneLaunchRunSuccess":
    return _launch_pipeline_execution(graphene_info, execution_params)


def do_launch(
    graphene_info: "ResolveInfo", execution_params: ExecutionParams, is_reexecuted: bool = False
) -> DagsterRun:
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, "execution_metadata", ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, "root_run_id")
        check.str_param(execution_metadata.parent_run_id, "parent_run_id")
    remote_job = get_remote_job_or_raise(graphene_info, execution_params.selector)
    code_location = graphene_info.context.get_code_location(execution_params.selector.location_name)
    dagster_run = create_valid_pipeline_run(
        graphene_info.context, remote_job, execution_params, code_location
    )

    return graphene_info.context.instance.submit_run(
        dagster_run.run_id,
        workspace=graphene_info.context,
    )


def _launch_pipeline_execution(
    graphene_info: "ResolveInfo", execution_params: ExecutionParams, is_reexecuted: bool = False
) -> "GrapheneLaunchRunSuccess":
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun
    from dagster_graphql.schema.runs import GrapheneLaunchRunSuccess

    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    run = do_launch(graphene_info, execution_params, is_reexecuted)
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))

    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))


def launch_reexecution_from_parent_run(
    graphene_info: "ResolveInfo",
    parent_run_id: str,
    strategy: str,
    extra_tags: Optional[Mapping[str, Any]] = None,
    use_parent_run_tags: Optional[bool] = None,
) -> "GrapheneLaunchRunSuccess":
    """Launch a re-execution by referencing the parent run id."""
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun
    from dagster_graphql.schema.runs import GrapheneLaunchRunSuccess

    check.str_param(parent_run_id, "parent_run_id")

    instance: DagsterInstance = graphene_info.context.instance
    parent_run = check.not_none(
        instance.get_run_by_id(parent_run_id), f"Could not find parent run with id: {parent_run_id}"
    )
    origin = check.not_none(parent_run.remote_job_origin)
    selector = JobSubsetSelector(
        location_name=origin.repository_origin.code_location_origin.location_name,
        repository_name=origin.repository_origin.repository_name,
        job_name=parent_run.job_name,
        asset_selection=parent_run.asset_selection,
        asset_check_selection=parent_run.asset_check_selection,
        op_selection=None,
    )

    assert_permission_for_location(
        graphene_info,
        Permissions.LAUNCH_PIPELINE_REEXECUTION,
        selector.location_name,
    )

    repo_location = graphene_info.context.get_code_location(selector.location_name)
    external_pipeline = get_remote_job_or_raise(graphene_info, selector)

    run = instance.create_reexecuted_run(
        parent_run=cast(DagsterRun, parent_run),
        code_location=repo_location,
        remote_job=external_pipeline,
        strategy=ReexecutionStrategy(strategy),
        extra_tags=extra_tags,
        use_parent_run_tags=use_parent_run_tags
        if use_parent_run_tags is not None
        else True,  # inherit whatever tags were set on the parent run at launch time
    )
    graphene_info.context.instance.submit_run(
        run.run_id,
        workspace=graphene_info.context,
    )

    # return run with updateTime
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))
    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))
