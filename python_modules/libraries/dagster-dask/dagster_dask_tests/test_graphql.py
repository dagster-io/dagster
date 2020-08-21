from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION, SUBSCRIPTION_QUERY
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.schema import create_schema
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector
from graphql import graphql
from graphql.execution.executors.sync import SyncExecutor

from dagster.cli.workspace import Workspace
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import RepositoryLocationHandle
from dagster.core.instance import DagsterInstance
from dagster.utils import file_relative_path


def test_execute_hammer_through_dagit():
    recon_repo = ReconstructableRepository.for_file(
        file_relative_path(__file__, '../../../dagster-test/dagster_test/toys/hammer.py'),
        'hammer_pipeline',
    )
    instance = DagsterInstance.local_temp()

    context = DagsterGraphQLContext(
        workspace=Workspace(
            [RepositoryLocationHandle.create_in_process_location(recon_repo.pointer)]
        ),
        instance=instance,
    )

    selector = infer_pipeline_selector(context, 'hammer_pipeline')

    executor = SyncExecutor()

    variables = {
        'executionParams': {
            'runConfigData': {
                'storage': {'filesystem': {}},
                'execution': {'dask': {'config': {'cluster': {'local': {}}}}},
            },
            'selector': selector,
            'mode': 'default',
        }
    }

    start_pipeline_result = graphql(
        request_string=LAUNCH_PIPELINE_EXECUTION_MUTATION,
        schema=create_schema(),
        context=context,
        variables=variables,
        executor=executor,
    )

    if start_pipeline_result.errors:
        raise Exception('{}'.format(start_pipeline_result.errors))

    run_id = start_pipeline_result.data['launchPipelineExecution']['run']['runId']

    context.drain_outstanding_executions()

    subscription = execute_dagster_graphql(context, SUBSCRIPTION_QUERY, variables={'runId': run_id})

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    messages = [x['__typename'] for x in subscribe_results[0].data['pipelineRunLogs']['messages']]

    assert 'PipelineStartEvent' in messages
    assert 'PipelineSuccessEvent' in messages
