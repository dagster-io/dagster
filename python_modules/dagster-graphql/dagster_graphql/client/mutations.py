from dagster.core.errors import DagsterError

from dagster_graphql.cli import execute_query

from .query import START_PIPELINE_EXECUTION_QUERY
from .util import HANDLED_EVENTS, dagster_event_from_dict


class DagsterGraphQLClientError(DagsterError):
    '''Indicates that some error has occurred when executing a GraphQL query against
    dagster-graphql'''


def execute_start_pipeline_execution_query(handle, variables):
    res = execute_query(
        handle,
        START_PIPELINE_EXECUTION_QUERY,
        variables,
        raise_on_error=True,
        use_sync_executor=True,
    )
    handle_start_pipeline_execution_errors(res)
    return handle_start_pipeline_execution_result(res)


def handle_start_pipeline_execution_errors(res):
    if res is None:
        raise DagsterGraphQLClientError('Unhandled error type. Raw response: {}'.format(res))

    if res.get('errors'):
        raise DagsterGraphQLClientError(
            'Internal error in GraphQL request. Response: {}'.format(res)
        )

    if not res.get('data', {}).get('startPipelineExecution', {}).get('__typename'):
        raise DagsterGraphQLClientError('Unexpected response type. Response: {}'.format(res))


def handle_start_pipeline_execution_result(res):
    res_data = res['data']['startPipelineExecution']

    res_type = res_data['__typename']

    if res_type == 'InvalidStepError':
        raise DagsterGraphQLClientError(
            'invalid step {step_key}'.format(step_key=res_data['invalidStepKey'])
        )

    if res_type == 'InvalidOutputError':
        raise DagsterGraphQLClientError(
            'invalid output {output} for step {step_key}'.format(
                output=res_data['invalidOutputName'], step_key=res_data['stepKey']
            )
        )

    if res_type == 'PipelineConfigValidationInvalid':
        errors = [err['message'] for err in res_data['errors']]
        raise DagsterGraphQLClientError(
            'Pipeline configuration invalid:\n{errors}'.format(errors='\n'.join(errors))
        )

    if res_type == 'PipelineNotFoundError':
        raise DagsterGraphQLClientError(
            'Pipeline "{pipeline_name}" not found: {message}:'.format(
                pipeline_name=res_data['pipelineName'], message=res_data['message']
            )
        )

    if res_type == 'PythonError':
        raise DagsterGraphQLClientError(
            'Subplan execution failed: {message}\n{stack}'.format(
                message=res_data['message'], stack=res_data['stack']
            )
        )

    if res_type == 'StartPipelineExecutionSuccess':
        pipeline_name = res_data['run']['pipeline']['name']

        skip_events = {
            'LogMessageEvent',
            'PipelineStartEvent',
            'PipelineSuccessEvent',
            'PipelineInitFailureEvent',
            'PipelineFailureEvent',
        }

        return [
            dagster_event_from_dict(e, pipeline_name)
            for e in res_data['run']['logs']['nodes']
            if e['__typename'] in HANDLED_EVENTS
        ]

    raise DagsterGraphQLClientError('Unexpected result type')
