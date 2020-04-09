from __future__ import absolute_import

from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check
from dagster.core.execution.api import create_execution_plan

from ..fetch_pipelines import get_pipeline_def_from_selector
from ..fetch_runs import get_validated_config
from ..utils import ExecutionMetadata, ExecutionParams, capture_dauphin_error
from .utils import _check_start_pipeline_execution_errors, _create_pipeline_run


@capture_dauphin_error
def launch_pipeline_reexecution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_dauphin_error
def launch_pipeline_execution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params)


def _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, 'execution_metadata', ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, 'root_run_id')
        check.str_param(execution_metadata.parent_run_id, 'parent_run_id')

    error_type = 'RunLauncherNotDefinedError'
    success_type = (
        'LaunchPipelineExecutionSuccess'
        if not is_reexecuted
        else 'LaunchPipelineReexecutionSuccess'
    )
    instance = graphene_info.context.instance
    run_launcher = instance.run_launcher

    if run_launcher is None:
        return graphene_info.schema.type_named(error_type)()

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        graphene_info,
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode, previous_run_id=execution_params.previous_run_id
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    run = instance.launch_run(_create_pipeline_run(instance, pipeline_def, execution_params))

    return graphene_info.schema.type_named(success_type)(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )
