from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import define_context_for_repository_yaml, execute_dagster_graphql

from dagster import seven
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.utils import make_new_run_id
from dagster.utils import file_relative_path

from .execution_queries import (
    START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
    START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
)
from .setup import (
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    define_test_context,
)
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


def sanitize_result_data(result_data):
    if isinstance(result_data, dict):
        if 'path' in result_data:
            result_data['path'] = 'DUMMY_PATH'
        result_data = {k: sanitize_result_data(v) for k, v in result_data.items()}
    elif isinstance(result_data, list):
        for i in range(len(result_data)):
            result_data[i] = sanitize_result_data(result_data[i])
    else:
        pass
    return result_data


def test_full_pipeline_reexecution_fs_storage(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    result_one = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result_one.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'

    snapshot.assert_match(sanitize_result_data(result_one.data))

    # reexecution
    new_run_id = make_new_run_id()

    result_two = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                },
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['startPipelineReexecution']
    assert query_result['__typename'] == 'StartPipelineRunSuccess'
    assert query_result['run']['rootRunId'] == run_id
    assert query_result['run']['parentRunId'] == run_id


def test_full_pipeline_reexecution_in_memory_storage(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    result_one = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result_one.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'

    snapshot.assert_match(sanitize_result_data(result_one.data))

    # reexecution
    new_run_id = make_new_run_id()

    result_two = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                },
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['startPipelineReexecution']
    assert query_result['__typename'] == 'StartPipelineRunSuccess'
    assert query_result['run']['rootRunId'] == run_id
    assert query_result['run']['parentRunId'] == run_id


def test_pipeline_reexecution_successful_launch():
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

    run_id = make_new_run_id()
    result = execute_dagster_graphql(
        context=context,
        query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            'executionParams': {
                'selector': {'name': 'no_config_pipeline'},
                'environmentConfigData': {'storage': {'filesystem': {}}},
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result.data['launchPipelineExecution']['__typename'] == 'LaunchPipelineRunSuccess'
    assert result.data['launchPipelineExecution']['run']['status'] == 'NOT_STARTED'
    test_queue.run_one(instance)
    result = execute_dagster_graphql(context=context, query=RUN_QUERY, variables={'runId': run_id})
    assert result.data['pipelineRunOrError']['__typename'] == 'PipelineRun'
    assert result.data['pipelineRunOrError']['status'] == 'SUCCESS'

    # reexecution
    new_run_id = make_new_run_id()
    result = execute_dagster_graphql(
        context=context,
        query=LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            'executionParams': {
                'selector': {'name': 'no_config_pipeline'},
                'environmentConfigData': {'storage': {'filesystem': {}}},
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                },
                'mode': 'default',
            }
        },
    )
    assert result.data['launchPipelineReexecution']['__typename'] == 'LaunchPipelineRunSuccess'

    test_queue.run_one(instance)

    result = execute_dagster_graphql(
        context=context, query=RUN_QUERY, variables={'runId': new_run_id}
    )
    assert result.data['pipelineRunOrError']['__typename'] == 'PipelineRun'
    assert result.data['pipelineRunOrError']['status'] == 'SUCCESS'


def test_pipeline_reexecution_launcher_missing():
    context = define_context_for_repository_yaml(
        path=file_relative_path(__file__, '../repository.yaml')
    )

    run_id = make_new_run_id()
    new_run_id = make_new_run_id()

    result = execute_dagster_graphql(
        context=context,
        query=LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        variables={
            'executionParams': {
                'selector': {'name': 'no_config_pipeline'},
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                },
                'mode': 'default',
            }
        },
    )

    assert result.data['launchPipelineReexecution']['__typename'] == 'RunLauncherNotDefinedError'
