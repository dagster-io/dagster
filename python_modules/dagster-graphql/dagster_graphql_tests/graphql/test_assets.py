import time

from dagster_graphql.test.utils import define_context_for_file, execute_dagster_graphql

from dagster import (
    Materialization,
    Output,
    RepositoryDefinition,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage

GET_ASSET_KEY_QUERY = '''
{
    assetsOrError {
        __typename
        ...on AssetConnection {
            nodes {
                key
            }
        }
    }
}
'''

GET_ASSET_MATERIALIZATION = '''
    query AssetQuery($assetKey: String!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(limit: 1) {
                    materializationEvent {
                        materialization {
                            label
                        }
                    }
                }
            }
        }
    }
'''

GET_ASSET_RUNS = '''
    query AssetRunsQuery($assetKey: String!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                runs {
                    runId
                }
            }
        }
    }
'''


def get_instance(temp_dir):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=InMemoryEventLogStorage(),
        compute_log_manager=NoOpComputeLogManager(temp_dir),
    )


def asset_repo():
    @solid
    def solid_a(_):
        yield Materialization(asset_key='a', label='a')
        yield Output(1)

    @solid
    def solid_b(_, num):
        yield Materialization(asset_key='b', label='b')
        time.sleep(0.1)
        yield Materialization(asset_key='c', label='c')
        yield Output(num)

    @pipeline
    def single_asset_pipeline():
        solid_a()

    @pipeline
    def multi_asset_pipeline():
        solid_b(solid_a())

    return RepositoryDefinition(
        'asset_repo', pipeline_defs=[single_asset_pipeline, multi_asset_pipeline]
    )


def test_get_all_asset_keys(snapshot):
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        repo = asset_repo()
        execute_pipeline(repo.get_pipeline('multi_asset_pipeline'), instance=instance)
        context = define_context_for_file(__file__, 'asset_repo', instance)
        result = execute_dagster_graphql(context, GET_ASSET_KEY_QUERY)
        assert result.data
        snapshot.assert_match(result.data)


def test_get_asset_key_materialization(snapshot):
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        repo = asset_repo()
        execute_pipeline(repo.get_pipeline('single_asset_pipeline'), instance=instance)
        context = define_context_for_file(__file__, 'asset_repo', instance)
        result = execute_dagster_graphql(
            context, GET_ASSET_MATERIALIZATION, variables={'assetKey': 'a'}
        )
        assert result.data
        snapshot.assert_match(result.data)


def test_get_asset_runs():
    with seven.TemporaryDirectory() as temp_dir:
        instance = get_instance(temp_dir)
        repo = asset_repo()
        single_run_id = execute_pipeline(
            repo.get_pipeline('single_asset_pipeline'), instance=instance
        ).run_id
        multi_run_id = execute_pipeline(
            repo.get_pipeline('multi_asset_pipeline'), instance=instance
        ).run_id
        context = define_context_for_file(__file__, 'asset_repo', instance)
        result = execute_dagster_graphql(context, GET_ASSET_RUNS, variables={'assetKey': 'a'})
        assert result.data
        fetched_runs = [run['runId'] for run in result.data['assetOrError']['runs']]
        assert len(fetched_runs) == 2
        assert multi_run_id in fetched_runs
        assert single_run_id in fetched_runs
