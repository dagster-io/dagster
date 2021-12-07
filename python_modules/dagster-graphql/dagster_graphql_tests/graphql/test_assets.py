import os
import time

from dagster import AssetKey
from dagster.utils import safe_tempfile_path
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_pipeline_selector,
    infer_repository_selector,
)

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

GET_ASSET_KEY_QUERY = """
    query AssetKeyQuery {
        assetsOrError {
            __typename
            ...on AssetConnection {
                nodes {
                    key {
                        path
                    }
                }
            }
        }
    }
"""

GET_ASSET_MATERIALIZATION = """
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(limit: 1) {
                    materializationEvent {
                        materialization {
                            label
                        }
                        assetLineage {
                            assetKey {
                                path
                            }
                            partitions
                        }
                    }
                }
                tags {
                    key
                    value
                }
            }
            ... on AssetNotFoundError {
                __typename
            }
        }
    }
"""

GET_ASSET_MATERIALIZATION_WITH_PARTITION = """
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(limit: 1) {
                    partition
                    materializationEvent {
                        materialization {
                            label
                        }
                    }
                }
            }
        }
    }
"""


WIPE_ASSETS = """
    mutation AssetKeyWipe($assetKeys: [AssetKeyInput!]!) {
        wipeAssets(assetKeys: $assetKeys) {
            __typename
        }
    }
"""

GET_ASSET_MATERIALIZATION_TIMESTAMP = """
    query AssetQuery($assetKey: AssetKeyInput!, $asOf: String) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(beforeTimestampMillis: $asOf) {
                    materializationEvent {
                        timestamp
                    }
                }
            }
        }
    }
"""

GET_ASSET_IN_PROGRESS_RUNS = """
    query AssetGraphQuery($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
            ... on Repository {
                assetNodes {
                    opName
                    description
                    jobName
                }
                inProgressRunsByStep {
                    stepKey
                    unstartedRuns {
                        runId
                    }
                    inProgressRuns {
                        runId
                    }
                }
            }
        }
    }
"""

GET_ASSET_NODES_FROM_KEYS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
        pipelineOrError(params: $pipelineSelector) {
            ... on Pipeline {
                id
                assetNodes(assetKeys: $assetKeys) {
                    id
                }
            }
        }
    }
"""


def _create_run(graphql_context, pipeline_name, mode="default"):
    selector = infer_pipeline_selector(graphql_context, pipeline_name)
    result = execute_dagster_graphql(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
                "mode": mode,
            }
        },
    )
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    graphql_context.instance.run_launcher.join()
    return result.data["launchPipelineExecution"]["run"]["runId"]


class TestAssetAwareEventLog(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.consolidated_sqlite_instance_managed_grpc_env(),
            GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(),
            GraphQLContextVariant.postgres_with_default_run_launcher_managed_grpc_env(),
        ]
    )
):
    def test_all_asset_keys(self, graphql_context, snapshot):
        _create_run(graphql_context, "multi_asset_pipeline")
        result = execute_dagster_graphql(graphql_context, GET_ASSET_KEY_QUERY)
        assert result.data
        assert result.data["assetsOrError"]
        assert result.data["assetsOrError"]["nodes"]

        # sort by materialization asset key to keep list order is consistent for snapshot
        result.data["assetsOrError"]["nodes"].sort(key=lambda e: e["key"]["path"][0])

        snapshot.assert_match(result.data)

    def test_get_asset_key_materialization(self, graphql_context, snapshot):
        _create_run(graphql_context, "single_asset_pipeline")
        result = execute_dagster_graphql(
            graphql_context, GET_ASSET_MATERIALIZATION, variables={"assetKey": {"path": ["a"]}}
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_asset_key_not_found(self, graphql_context, snapshot):
        _create_run(graphql_context, "single_asset_pipeline")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["bogus", "asset"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_partitioned_asset_key_materialization(self, graphql_context, snapshot):
        _create_run(graphql_context, "partitioned_asset_pipeline")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_WITH_PARTITION,
            variables={"assetKey": {"path": ["a"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_asset_key_lineage(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "asset_lineage_pipeline")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["b"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_partitioned_asset_key_lineage(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "partitioned_asset_lineage_pipeline")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["b"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_asset_wipe(self, graphql_context):
        _create_run(graphql_context, "single_asset_pipeline")
        _create_run(graphql_context, "multi_asset_pipeline")

        asset_keys = graphql_context.instance.all_asset_keys()
        assert AssetKey("a") in asset_keys

        result = execute_dagster_graphql(
            graphql_context, WIPE_ASSETS, variables={"assetKeys": [{"path": ["a"]}]}
        )

        assert result.data
        assert result.data["wipeAssets"]
        assert result.data["wipeAssets"]["__typename"] == "AssetWipeSuccess"

        asset_keys = graphql_context.instance.all_asset_keys()
        assert AssetKey("a") not in asset_keys

    def test_asset_tags(self, graphql_context, snapshot):
        _create_run(graphql_context, "asset_tag_pipeline")
        result = execute_dagster_graphql(
            graphql_context, GET_ASSET_MATERIALIZATION, variables={"assetKey": {"path": ["a"]}}
        )
        assert result.data
        assert result.data["assetOrError"]
        assert result.data["assetOrError"]["tags"]
        snapshot.assert_match(result.data)

    def test_asset_asof_timestamp(self, graphql_context):
        _create_run(graphql_context, "asset_tag_pipeline")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_TIMESTAMP,
            variables={"assetKey": {"path": ["a"]}},
        )
        assert result.data
        assert result.data["assetOrError"]
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 1
        first_timestamp = int(materializations[0]["materializationEvent"]["timestamp"])

        as_of_timestamp = first_timestamp + 1

        time.sleep(1.1)
        _create_run(graphql_context, "asset_tag_pipeline")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_TIMESTAMP,
            variables={"assetKey": {"path": ["a"]}},
        )
        assert result.data
        assert result.data["assetOrError"]
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 2
        second_timestamp = int(materializations[0]["materializationEvent"]["timestamp"])

        assert second_timestamp > as_of_timestamp

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_TIMESTAMP,
            variables={"assetKey": {"path": ["a"]}, "asOf": as_of_timestamp},
        )
        assert result.data
        assert result.data["assetOrError"]
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 1
        assert first_timestamp == int(materializations[0]["materializationEvent"]["timestamp"])

    def test_asset_node_in_pipeline(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={"pipelineSelector": selector, "assetKeys": [{"path": ["asset_one"]}]},
        )

        assert result.data
        assert result.data["pipelineOrError"]
        assert result.data["pipelineOrError"]["assetNodes"]

        assert len(result.data["pipelineOrError"]["assetNodes"]) == 1
        asset_node = result.data["pipelineOrError"]["assetNodes"][0]
        assert asset_node["id"] == '["asset_one"]'

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["pipelineOrError"]
        assert result.data["pipelineOrError"]["assetNodes"]

        assert len(result.data["pipelineOrError"]["assetNodes"]) == 2
        asset_node = result.data["pipelineOrError"]["assetNodes"][0]
        assert asset_node["id"] == '["asset_one"]'


class TestPersistentInstanceAssetInProgress(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(),
            GraphQLContextVariant.postgres_with_default_run_launcher_managed_grpc_env(),
        ]
    )
):
    def test_asset_in_progress(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "hanging_job")
        run_id = "foo"

        with safe_tempfile_path() as path:
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {
                            "resources": {"hanging_asset_resource": {"config": {"file": path}}}
                        },
                        "executionMetadata": {"runId": run_id},
                    }
                },
            )

            assert not result.errors
            assert result.data

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context,
                GET_ASSET_IN_PROGRESS_RUNS,
                variables={"repositorySelector": infer_repository_selector(graphql_context)},
            )
            graphql_context.instance.run_launcher.terminate(run_id)

            assert result.data
            assert result.data["repositoryOrError"]
            assert result.data["repositoryOrError"]["inProgressRunsByStep"]

            in_progress_runs_by_step = result.data["repositoryOrError"]["inProgressRunsByStep"]

            assert len(in_progress_runs_by_step) == 2

            hanging_asset_status = in_progress_runs_by_step[0]
            never_runs_asset_status = in_progress_runs_by_step[1]
            # graphql endpoint returns unordered list of steps
            # swap if never_runs_asset_status is first in list
            if hanging_asset_status["stepKey"] != "hanging_asset":
                never_runs_asset_status, hanging_asset_status = (
                    hanging_asset_status,
                    never_runs_asset_status,
                )

            assert hanging_asset_status["stepKey"] == "hanging_asset"
            assert len(hanging_asset_status["inProgressRuns"]) == 1
            assert hanging_asset_status["inProgressRuns"][0]["runId"] == run_id
            assert len(hanging_asset_status["unstartedRuns"]) == 0

            assert never_runs_asset_status["stepKey"] == "never_runs_asset"
            assert len(never_runs_asset_status["inProgressRuns"]) == 0
            assert len(never_runs_asset_status["unstartedRuns"]) == 1
            assert never_runs_asset_status["unstartedRuns"][0]["runId"] == run_id
