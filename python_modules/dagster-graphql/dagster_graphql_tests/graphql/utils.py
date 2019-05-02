from .execution_queries import START_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY
from .setup import define_context, execute_dagster_graphql


def sync_execute_get_run_log_data(variables, raise_on_error=True):
    context = define_context(raise_on_error=raise_on_error)
    result = execute_dagster_graphql(context, START_PIPELINE_EXECUTION_QUERY, variables=variables)

    assert result.data

    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    run_id = result.data['startPipelineExecution']['run']['runId']

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]
    assert not subscribe_result.errors
    assert subscribe_result.data
    assert subscribe_result.data['pipelineRunLogs']
    return subscribe_result.data['pipelineRunLogs']


def sync_execute_get_events(variables):
    return sync_execute_get_run_log_data(variables)['messages']
