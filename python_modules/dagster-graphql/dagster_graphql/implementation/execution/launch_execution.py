from graphql.execution.base import ResolveInfo

import dagster._check as check
from dagster.core.execution.plan.resume_retry import ReexecutionStrategy
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import RunsFilter

from ..external import get_external_pipeline_or_raise
from ..utils import ExecutionMetadata, ExecutionParams, capture_error
from .run_lifecycle import create_valid_pipeline_run


@capture_error
def launch_pipeline_reexecution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_error
def launch_pipeline_execution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params)


def do_launch(graphene_info, execution_params, is_reexecuted=False):
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


def _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.runs import GrapheneLaunchRunSuccess

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    run = do_launch(graphene_info, execution_params, is_reexecuted)
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))

    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))


@capture_error
def launch_reexecution_from_parent_run(graphene_info, parent_run_id: str, strategy):
    """
    Launch a re-execution by referencing the parent run id
    """
    from ...schema.pipelines.pipeline import GrapheneRun
    from ...schema.runs import GrapheneLaunchRunSuccess

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(parent_run_id, "parent_run_id")
    check.str_param(strategy, "strategy")

    instance: DagsterInstance = graphene_info.context.instance
    parent_run = instance.get_run_by_id(parent_run_id)
    check.invariant(parent_run, "Could not find parent run with id: %s" % parent_run_id)

    selector = PipelineSelector(
        location_name=parent_run.external_pipeline_origin.external_repository_origin.repository_location_origin.location_name,
        repository_name=parent_run.external_pipeline_origin.external_repository_origin.repository_name,
        pipeline_name=parent_run.pipeline_name,
        solid_selection=None,
    )

    repo_location = graphene_info.context.get_repository_location(selector.location_name)
    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)

    run = instance.create_reexecuted_run(
        parent_run,
        repo_location,
        external_pipeline,
        ReexecutionStrategy[strategy],
        use_parent_run_tags=True,  # inherit whatever tags were set on the parent run at launch time
    )
    graphene_info.context.instance.submit_run(
        run.run_id,
        workspace=graphene_info.context,
    )

    # return run with updateTime
    records = graphene_info.context.instance.get_run_records(RunsFilter(run_ids=[run.run_id]))
    return GrapheneLaunchRunSuccess(run=GrapheneRun(records[0]))
