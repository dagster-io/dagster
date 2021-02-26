from dagster import check
from graphql.execution.base import ResolveInfo

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
        pipeline_run.run_id, external_pipeline=external_pipeline
    )


def _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    from ...schema.pipelines.pipeline import GraphenePipelineRun
    from ...schema.runs import GrapheneLaunchPipelineRunSuccess

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    check.bool_param(is_reexecuted, "is_reexecuted")

    run = do_launch(graphene_info, execution_params, is_reexecuted)

    return GrapheneLaunchPipelineRunSuccess(run=GraphenePipelineRun(run))
