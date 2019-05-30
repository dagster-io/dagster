from dagster_graphql.test.utils import execute_dagster_graphql
from .execution_queries import START_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY
from .setup import define_context


def sync_execute_get_payload(variables, raise_on_error=True, context=None):
    if not context:
        context = define_context(raise_on_error=raise_on_error)

    result = execute_dagster_graphql(context, START_PIPELINE_EXECUTION_QUERY, variables=variables)

    assert result.data

    if result.data['startPipelineExecution']['__typename'] != 'StartPipelineExecutionSuccess':
        raise Exception(result.data)
    run_id = result.data['startPipelineExecution']['run']['runId']

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]
    assert not subscribe_result.errors
    assert subscribe_result.data
    return subscribe_result.data


def sync_execute_get_run_log_data(variables, raise_on_error=True, context=None):
    payload_data = sync_execute_get_payload(
        variables, raise_on_error=raise_on_error, context=context
    )
    assert payload_data['pipelineRunLogs']
    return payload_data['pipelineRunLogs']


def sync_execute_get_events(variables, context=None):
    return sync_execute_get_run_log_data(variables, context=context)['messages']
