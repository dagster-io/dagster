from dagster_graphql.client.query import SUBSCRIPTION_QUERY
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .execution_queries import START_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY
from .setup import define_context


def sync_execute_get_payload(variables, context=None):
    context = (
        context if context is not None else define_context(instance=DagsterInstance.local_temp())
    )

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


def sync_execute_get_run_log_data(variables,):
    payload_data = sync_execute_get_payload(variables)
    assert payload_data['pipelineRunLogs']
    return payload_data['pipelineRunLogs']


def sync_execute_get_events(variables):
    return sync_execute_get_run_log_data(variables)['messages']
