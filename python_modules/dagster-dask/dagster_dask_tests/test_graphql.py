from dagster_graphql.client.query import START_PIPELINE_EXECUTION_MUTATION, SUBSCRIPTION_QUERY
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SubprocessExecutionManager
from dagster_graphql.schema import create_schema
from dagster_graphql.test.utils import execute_dagster_graphql
from graphql import graphql
from graphql.execution.executors.sync import SyncExecutor

from dagster import ExecutionTargetHandle
from dagster.core.instance import DagsterInstance
from dagster.utils import script_relative_path


def test_execute_hammer_through_dagit():
    handle = ExecutionTargetHandle.for_pipeline_python_file(
        script_relative_path('../../../examples/dagster_examples/toys/hammer.py'), 'hammer_pipeline'
    )
    instance = DagsterInstance.local_temp()

    execution_manager = SubprocessExecutionManager(instance)

    context = DagsterGraphQLContext(
        handle=handle, execution_manager=execution_manager, instance=instance
    )

    executor = SyncExecutor()

    variables = {
        'executionParams': {
            'environmentConfigData': {'storage': {'filesystem': {}}, 'execution': {'dask': {}}},
            'selector': {'name': handle.build_pipeline_definition().name},
            'mode': 'default',
        }
    }

    start_pipeline_result = graphql(
        request_string=START_PIPELINE_EXECUTION_MUTATION,
        schema=create_schema(),
        context=context,
        variables=variables,
        executor=executor,
    )

    run_id = start_pipeline_result.data['startPipelineExecution']['run']['runId']

    context.execution_manager.join()

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    messages = [x['__typename'] for x in subscribe_results[0].data['pipelineRunLogs']['messages']]

    assert 'PipelineProcessStartEvent' in messages
    assert 'PipelineProcessStartedEvent' in messages
    assert 'PipelineStartEvent' in messages
    assert 'PipelineSuccessEvent' in messages
    assert 'PipelineProcessExitedEvent' in messages
