from __future__ import absolute_import

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.execution.api import execute_run
from dagster.utils.hosted_user_process import pipeline_def_from_pipeline_handle

from ..utils import ExecutionParams, capture_dauphin_error
from .launch_execution import do_launch
from .run_lifecycle import RunExecutionInfo, get_run_execution_info_for_created_run_or_error


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params):
    '''This indirection done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _start_pipeline_execution(graphene_info, execution_params)


def _start_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    check.invariant(
        graphene_info.context.instance.run_launcher,
        'Should always be true. '
        'The reign of the execution manager is over. The time of the run launcher has come.',
    )

    run = do_launch(graphene_info, execution_params, is_reexecuted)

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


@capture_dauphin_error
def start_pipeline_execution_for_created_run(graphene_info, run_id):
    '''This indirection is done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id)


def _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id):
    prepare_launch_result = get_run_execution_info_for_created_run_or_error(graphene_info, run_id)

    if not isinstance(prepare_launch_result, RunExecutionInfo):
        # if it is not a success the return value is the dauphin error
        return prepare_launch_result

    external_pipeline, pipeline_run = prepare_launch_result
    pipeline_def = pipeline_def_from_pipeline_handle(external_pipeline.handle)
    execute_run(pipeline_def, pipeline_run, graphene_info.context.instance)

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
