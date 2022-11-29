from typing import cast

from dagster_graphql.schema.runs import GrapheneLaunchRunSuccess
from dagster_graphql.schema.util import HasContext
from graphene import ResolveInfo

import dagster._check as check
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.host_representation.selector import PipelineSelector
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun, PipelineRun, RunsFilter

from ..external import get_external_pipeline_or_raise
from ..utils import ExecutionMetadata, ExecutionParams, capture_error
from .run_lifecycle import create_valid_pipeline_run


@capture_error
def launch_pipeline_reexecution(
    graphene_info: HasContext, execution_params: ExecutionParams
) -> GrapheneLaunchRunSuccess:
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_error
def launch_pipeline_execution(
    graphene_info: HasContext, execution_params: ExecutionParams
) -> GrapheneLaunchRunSuccess:
    return _launch_pipeline_execution(graphene_info, execution_params)


def do_launch(
    graphene_info: HasContext, execution_params: ExecutionParams, is_reexecuted: bool = False
) -> PipelineRun:
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, "execution_metadata", ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, "root_run_id")
        check.str_param(execution_metadata.parent_run_id, "parent_run_id")
    external_pipeline = get_external_pipeline_or_raise(graphene_info, execution_params.selector)
    pipeline_run = create_valid_pipeline_run(graphene_info, external_pipeline, execution_params)

    return graphene_info.context.instance.submit_run(
        pipeline_run.run_id,
        workspace=graphene_info.context,
    )


def _launch_pipeline_execution(
    graphene_info, execution_params: ExecutionParams, is_reexecuted: bool = False
) -> GrapheneLaunchRunSuccess:
    from ...schema.pipelines.pipeline import GrapheneRun

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    run = do_launch(graphene_info, execution_params, is_reexecuted)
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))

    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))


@capture_error
def launch_reexecution_from_parent_run(
    graphene_info: HasContext, parent_run_id: str, strategy: str
) -> GrapheneLaunchRunSuccess:
    """
    Launch a re-execution by referencing the parent run id
    """
    from ...schema.pipelines.pipeline import GrapheneRun

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(parent_run_id, "parent_run_id")

    instance: DagsterInstance = graphene_info.context.instance
    parent_run = check.not_none(
        instance.get_run_by_id(parent_run_id), f"Could not find parent run with id: {parent_run_id}"
    )
    origin = check.not_none(parent_run.external_pipeline_origin)
    selector = PipelineSelector(
        location_name=origin.external_repository_origin.repository_location_origin.location_name,
        repository_name=origin.external_repository_origin.repository_name,
        pipeline_name=parent_run.pipeline_name,
        solid_selection=None,
    )

    repo_location = graphene_info.context.get_repository_location(selector.location_name)
    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)

    run = instance.create_reexecuted_run(
        cast(DagsterRun, parent_run),
        repo_location,
        external_pipeline,
        ReexecutionStrategy(strategy),
        use_parent_run_tags=True,  # inherit whatever tags were set on the parent run at launch time
    )
    graphene_info.context.instance.submit_run(
        run.run_id,
        workspace=graphene_info.context,
    )

    # return run with updateTime
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))
    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))
