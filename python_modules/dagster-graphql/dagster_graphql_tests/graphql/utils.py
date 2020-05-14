from dagster_graphql.client.query import SUBSCRIPTION_QUERY
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.execution.api import execute_run_iterator
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher

from .execution_queries import START_PIPELINE_EXECUTION_QUERY, SUBSCRIPTION_QUERY
from .setup import define_repository, define_test_context


class InMemoryRunLauncher(RunLauncher):
    def __init__(self):
        self._queue = []

    def launch_run(self, instance, run):
        self._queue.append(run)
        return run

    def run_one(self, instance):
        assert len(self._queue) > 0
        run = self._queue.pop(0)
        pipeline_def = (
            define_repository().get_pipeline(run.pipeline_name).build_sub_pipeline(run.solid_subset)
        )
        return [
            ev
            for ev in execute_run_iterator(InMemoryExecutablePipeline(pipeline_def), run, instance)
        ]


def sync_get_all_logs_for_run(context, run_id):
    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})
    subscribe_results = []

    subscription.subscribe(subscribe_results.append)
    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]
    if subscribe_result.errors:
        raise Exception(subscribe_result.errors)
    assert not subscribe_result.errors
    assert subscribe_result.data
    return subscribe_result.data


def sync_execute_get_payload(variables, context=None):
    context = (
        context
        if context is not None
        else define_test_context(instance=DagsterInstance.local_temp())
    )

    result = execute_dagster_graphql(context, START_PIPELINE_EXECUTION_QUERY, variables=variables)

    assert result.data

    if result.data['startPipelineExecution']['__typename'] != 'StartPipelineRunSuccess':
        raise Exception(result.data)
    run_id = result.data['startPipelineExecution']['run']['runId']
    return sync_get_all_logs_for_run(context, run_id)


def sync_execute_get_run_log_data(variables):
    payload_data = sync_execute_get_payload(variables)
    assert payload_data['pipelineRunLogs']
    return payload_data['pipelineRunLogs']


def sync_execute_get_events(variables):
    return sync_execute_get_run_log_data(variables)['messages']
