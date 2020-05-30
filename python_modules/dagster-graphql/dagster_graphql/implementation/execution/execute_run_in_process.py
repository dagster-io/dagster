from dagster.core.execution.api import execute_run
from dagster.utils.hosted_user_process import recon_pipeline_from_pipeline_handle

from ..utils import capture_dauphin_error
from .run_lifecycle import RunExecutionInfo, get_run_execution_info_for_created_run_or_error


@capture_dauphin_error
def execute_run_in_graphql_process(graphene_info, run_id):
    '''This indirection is done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id)


def _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id):
    run_info_or_error = get_run_execution_info_for_created_run_or_error(graphene_info, run_id)

    if not isinstance(run_info_or_error, RunExecutionInfo):
        # if it is not a success the return value is the dauphin error
        return run_info_or_error

    external_pipeline, pipeline_run = run_info_or_error
    recon_pipeline = recon_pipeline_from_pipeline_handle(external_pipeline.handle)
    execute_run(recon_pipeline, pipeline_run, graphene_info.context.instance)
    return graphene_info.schema.type_named('ExecuteRunInProcessSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
