from dagster_graphql.cli import execute_query

from dagster.core.errors import DagsterError
from dagster.core.instance import DagsterInstance

from .query import EXECUTE_PLAN_MUTATION, START_PIPELINE_EXECUTION_MUTATION
from .util import HANDLED_EVENTS, dagster_event_from_dict


class DagsterGraphQLClientError(DagsterError):
    '''Indicates that some error has occurred when executing a GraphQL query against
    dagster-graphql'''


def execute_start_pipeline_execution_mutation(handle, variables, instance_ref=None):
    res = execute_query(
        handle,
        START_PIPELINE_EXECUTION_MUTATION,
        variables,
        raise_on_error=True,
        use_sync_executor=True,
        instance=DagsterInstance.from_ref(instance_ref, watch_external_runs=False)
        if instance_ref
        else DagsterInstance.ephemeral(),
    )
    handle_execution_errors(res, 'startPipelineExecution')
    return handle_start_pipeline_execution_result(res)


def execute_execute_plan_mutation(handle, variables, instance_ref=None):
    instance = (
        DagsterInstance.from_ref(instance_ref, watch_external_runs=False)
        if instance_ref
        else DagsterInstance.ephemeral()
    )
    res = execute_query(
        handle,
        EXECUTE_PLAN_MUTATION,
        variables,
        raise_on_error=True,
        use_sync_executor=True,
        instance=instance,
    )
    handle_execution_errors(res, 'executePlan')
    return handle_execute_plan_result(res)


def handle_execution_errors(res, expected_type):
    if res is None:
        raise DagsterGraphQLClientError('Unhandled error type. Raw response: {}'.format(res))

    if res.get('errors'):
        raise DagsterGraphQLClientError(
            'Internal error in GraphQL request. Response: {}'.format(res)
        )

    if not res.get('data', {}).get(expected_type, {}).get('__typename'):
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

        return [
            dagster_event_from_dict(e, pipeline_name)
            for e in res_data['run']['logs']['nodes']
            if e['__typename'] in HANDLED_EVENTS
        ]

    raise DagsterGraphQLClientError('Unexpected result type')


def handle_execute_plan_result(res):
    res_data = res['data']['executePlan']

    res_type = res_data['__typename']

    if res_type == 'InvalidStepError':
        raise DagsterGraphQLClientError(
            'invalid step {step_key}'.format(step_key=res_data['invalidStepKey'])
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

    if res_type == 'ExecutePlanSuccess':
        pipeline_name = res_data['pipeline']['name']

        return [
            dagster_event_from_dict(e, pipeline_name)
            for e in res_data['stepEvents']
            if e['__typename'] in HANDLED_EVENTS
        ]

    raise DagsterGraphQLClientError('Unexpected result type')
