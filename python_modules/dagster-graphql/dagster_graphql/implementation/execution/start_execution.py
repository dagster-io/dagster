from __future__ import absolute_import

from graphql.execution.base import ResolveInfo

from dagster import check

from ..utils import ExecutionParams, capture_dauphin_error
from .launch_execution import do_launch


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
