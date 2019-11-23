from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import seven
from dagster.core.execution.api import execute_run_iterator
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import RunLauncher
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils import script_relative_path

from .setup import define_context_for_repository_yaml, define_repository

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


class InMemoryRunLauncher(RunLauncher):
    def __init__(self):
        self._queue = []

    def launch_run(self, run):
        self._queue.append(run)
        return run

    def run_one(self, instance):
        assert len(self._queue) > 0
        run = self._queue.pop(0)
        pipeline = define_repository().get_pipeline(run.pipeline_name)
        return [ev for ev in execute_run_iterator(pipeline, run, instance)]


def test_missing():
    context = define_context_for_repository_yaml(path=script_relative_path('../repository.yaml'))

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
        path=script_relative_path('../repository.yaml'), instance=instance
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
