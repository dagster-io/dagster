from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils import file_relative_path

from .utils import InMemoryRunLauncher

RUN_QUERY = '''
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
        status
      }
    }
  }
'''


def test_missing():
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml')
    )

    result = execute_dagster_graphql(
        context=context,
        query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            'executionParams': {'selector': {'name': 'no_config_pipeline'}, 'mode': 'default'}
        },
    )

    assert result.data['launchPipelineExecution']['__typename'] == 'RunLauncherNotDefinedError'


def test_run_launcher():
    test_queue = InMemoryRunLauncher()

    with seven.TemporaryDirectory() as temp_dir:
        instance = DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=InMemoryRunStorage(),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(temp_dir),
            run_launcher=test_queue,
        )

    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml'), instance=instance
    )

    result = execute_dagster_graphql(
        context=context,
        query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            'executionParams': {'selector': {'name': 'no_config_pipeline'}, 'mode': 'default'}
        },
    )

    assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineExecutionSuccess'
    assert result.data['launchPipelineExecution']['run']['status'] == 'NOT_STARTED'

    run_id = result.data['launchPipelineExecution']['run']['runId']

    test_queue.run_one(instance)

    result = execute_dagster_graphql(context=context, query=RUN_QUERY, variables={'runId': run_id})
    assert result.data['pipelineRunOrError']['__typename'] == 'PipelineRun'
    assert result.data['pipelineRunOrError']['status'] == 'SUCCESS'
