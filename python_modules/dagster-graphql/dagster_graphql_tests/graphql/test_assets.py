import os
import time

from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_pipeline_selector,
    infer_repository_selector,
)

from dagster import AssetKey
from dagster.utils import safe_tempfile_path

# from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite
from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix

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
                    label
                    assetLineage {
                        assetKey {
                            path
                        }
                        partitions
                    }
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
                    label
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
                    timestamp
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
                    jobNames
                    description
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


GET_ASSET_LATEST_RUN_STATS = """
    query AssetGraphQuery($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
            ... on Repository {
                latestRunByStep{
                    ... on LatestRun {
                        stepKey
                        run {
                            runId
                        }
                    }
                    ... on JobRunsCount {
                        stepKey
                        jobNames
                        count
                        sinceLatestMaterialization
                    }
                }
            }
        }
    }
"""


GET_ASSET_NODES_FROM_KEYS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
        assetNodes(pipeline: $pipelineSelector, assetKeys: $assetKeys) {
            id
        }
    }
"""


GET_ASSET_PARTITIONS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            partitionKeys
        }
    }
"""

GET_LATEST_MATERIALIZATION_PER_PARTITION = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $partitions: [String!]) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            partitionKeys
            latestMaterializationByPartition(partitions: $partitions) {
                partition
                stepStats {
                    startTime
                }
            }
        }
    }
"""

GET_ASSET_OBSERVATIONS = """
    query AssetGraphQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetObservations {
                    label
                    description
                    runOrError {
                        ... on Run {
                            jobName
                        }
                    }
                    assetKey {
                        path
                    }
                    metadataEntries {
                        label
                        description
                        ... on TextMetadataEntry {
                            text
                        }
                    }
                }
            }
        }
    }
"""

GET_MATERIALIZATION_COUNT_BY_PARTITION = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            materializationCountByPartition {
                ... on MaterializationCountByPartition {
                    partition
                    materializationCount
                }
            }
        }
    }
"""

GET_ASSET_MATERIALIZATION_AFTER_TIMESTAMP = """
    query AssetQuery($assetKey: AssetKeyInput!, $afterTimestamp: String) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetMaterializations(afterTimestampMillis: $afterTimestamp) {
                    timestamp
                }
            }
        }
    }
"""

GET_ASSET_OP = """
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                definition {
                    op {
                        name
                        description
                        inputDefinitions {
                            name
                        }
                        outputDefinitions {
                            name
                        }
                    }
                }
            }
        }
    }
"""

GET_OP_ASSETS = """
    query OpQuery($repositorySelector: RepositorySelector!, $opName: String!) {
        repositoryOrError(repositorySelector: $repositorySelector) {
            ... on Repository {
                usedSolid(name: $opName) {
                    definition {
                        assetNodes {
                            assetKey {
                               path
                            }
                        }
                    }
                }
            }
        }
    }
"""


def _create_run(graphql_context, pipeline_name, mode="default", step_keys=None):
    selector = infer_pipeline_selector(graphql_context, pipeline_name)
    result = execute_dagster_graphql(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={"executionParams": {"selector": selector, "mode": mode, "stepKeys": step_keys}},
    )
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    graphql_context.instance.run_launcher.join()
    return result.data["launchPipelineExecution"]["run"]["runId"]


class TestAssetAwareEventLog(ExecutingGraphQLContextTestMatrix):
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
        first_timestamp = int(materializations[0]["timestamp"])

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
        second_timestamp = int(materializations[0]["timestamp"])

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
        assert first_timestamp == int(materializations[0]["timestamp"])

        # Test afterTimestamp before the first timestamp, which should return both results
        after_timestamp = first_timestamp - 1

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_AFTER_TIMESTAMP,
            variables={"assetKey": {"path": ["a"]}, "afterTimestamp": after_timestamp},
        )
        assert result.data
        assert result.data["assetOrError"]
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 2

        # Test afterTimestamp between the two timestamps, which should only return the first result
        after_timestamp = first_timestamp + 1

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_AFTER_TIMESTAMP,
            variables={"assetKey": {"path": ["a"]}, "afterTimestamp": after_timestamp},
        )
        assert result.data
        assert result.data["assetOrError"]
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 1
        assert second_timestamp == int(materializations[0]["timestamp"])

    def test_asset_node_in_pipeline(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={"pipelineSelector": selector, "assetKeys": [{"path": ["asset_one"]}]},
        )

        assert result.data
        assert result.data["assetNodes"]

        assert len(result.data["assetNodes"]) == 1
        asset_node = result.data["assetNodes"][0]
        assert asset_node["id"] == '["asset_one"]'

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]

        assert len(result.data["assetNodes"]) == 2
        asset_node = result.data["assetNodes"][0]
        assert asset_node["id"] == '["asset_one"]'

    def test_asset_partitions_in_pipeline(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 2
        asset_node = result.data["assetNodes"][0]
        assert asset_node["partitionKeys"] == []

        selector = infer_pipeline_selector(graphql_context, "static_partitioned_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 2
        asset_node = result.data["assetNodes"][0]
        assert asset_node["partitionKeys"] and asset_node["partitionKeys"] == [
            "a",
            "b",
            "c",
            "d",
        ]
        asset_node = result.data["assetNodes"][1]
        assert asset_node["partitionKeys"] and asset_node["partitionKeys"] == [
            "a",
            "b",
            "c",
            "d",
        ]

        selector = infer_pipeline_selector(graphql_context, "time_partitioned_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 2
        asset_node = result.data["assetNodes"][0]

        # test partition starts at "2021-05-05-01:00". Should be > 100 partition keys
        # since partition is hourly
        assert asset_node["partitionKeys"] and len(asset_node["partitionKeys"]) > 100
        assert asset_node["partitionKeys"][0] == "2021-05-05-01:00"
        assert asset_node["partitionKeys"][1] == "2021-05-05-02:00"

    def test_latest_materialization_per_partition(self, graphql_context):
        _create_run(graphql_context, "partition_materialization_job")

        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_MATERIALIZATION_PER_PARTITION,
            variables={"pipelineSelector": selector, "partitions": ["a"]},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        assert len(asset_node["latestMaterializationByPartition"]) == 1
        assert asset_node["latestMaterializationByPartition"][0] == None

        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_MATERIALIZATION_PER_PARTITION,
            variables={"pipelineSelector": selector, "partitions": ["c"]},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        assert len(asset_node["latestMaterializationByPartition"]) == 1
        materialization = asset_node["latestMaterializationByPartition"][0]
        start_time = materialization["stepStats"]["startTime"]
        assert materialization["partition"] == "c"

        _create_run(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_MATERIALIZATION_PER_PARTITION,
            variables={"pipelineSelector": selector, "partitions": ["c", "a"]},
        )
        assert result.data and result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        assert len(asset_node["latestMaterializationByPartition"]) == 2
        materialization = asset_node["latestMaterializationByPartition"][0]
        new_start_time = materialization["stepStats"]["startTime"]
        assert new_start_time > start_time

        assert asset_node["latestMaterializationByPartition"][1] == None

    def test_materialization_count_by_partition(self, graphql_context):
        # test for unpartitioned asset
        selector = infer_pipeline_selector(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_COUNT_BY_PARTITION,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]

        materialization_count = result.data["assetNodes"][0]["materializationCountByPartition"]
        assert len(materialization_count) == 0

        # test for partitioned asset with no materializations
        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_COUNT_BY_PARTITION,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]

        materialization_count_result = result.data["assetNodes"][0][
            "materializationCountByPartition"
        ]
        assert len(materialization_count_result) == 4
        for materialization_count in materialization_count_result:
            assert materialization_count["materializationCount"] == 0

        # test for partitioned asset with 1 materialization in 1 partition
        _create_run(graphql_context, "partition_materialization_job")

        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_COUNT_BY_PARTITION,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialization_count = asset_node["materializationCountByPartition"]

        assert len(materialization_count) == 4
        assert materialization_count[0]["partition"] == "a"
        assert materialization_count[0]["materializationCount"] == 0

        assert materialization_count[2]["partition"] == "c"
        assert materialization_count[2]["materializationCount"] == 1

        # test for partitioned asset with 2 materializations in 1 partition
        _create_run(graphql_context, "partition_materialization_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_COUNT_BY_PARTITION,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialization_count = asset_node["materializationCountByPartition"]

        assert len(materialization_count) == 4
        assert materialization_count[0]["partition"] == "a"
        assert materialization_count[0]["materializationCount"] == 0

        assert materialization_count[2]["partition"] == "c"
        assert materialization_count[2]["materializationCount"] == 2

    def test_asset_observations(self, graphql_context):
        _create_run(graphql_context, "observation_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_OBSERVATIONS,
            variables={"assetKey": {"path": ["asset_yields_observation"]}},
        )

        assert result.data
        assert result.data["assetOrError"]
        observations = result.data["assetOrError"]["assetObservations"]

        assert observations
        assert observations[0]["runOrError"]["jobName"] == "observation_job"

        asset_key_path = observations[0]["assetKey"]["path"]
        assert asset_key_path
        assert asset_key_path == ["asset_yields_observation"]

        metadata = observations[0]["metadataEntries"]
        assert metadata
        assert metadata[0]["text"] == "FOO"

        assert observations[0]["label"] == "asset_yields_observation"

    def test_asset_op(self, graphql_context, snapshot):
        _create_run(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_OP,
            variables={"assetKey": {"path": ["asset_two"]}},
        )

        assert result.data
        snapshot.assert_match(result.data)

    def test_op_assets(self, graphql_context, snapshot):
        _create_run(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_OP_ASSETS,
            variables={
                "repositorySelector": infer_repository_selector(graphql_context),
                "opName": "asset_two",
            },
        )

        assert result.data
        snapshot.assert_match(result.data)

    def test_latest_run_stats_by_asset(self, graphql_context):
        def get_response_by_step(response):
            return {stat["stepKey"]: stat for stat in response}

        selector = infer_repository_selector(graphql_context)

        # Confirm that when no runs are present, run returned is None
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["repositoryOrError"]
        assert result.data["repositoryOrError"]["latestRunByStep"]
        result = get_response_by_step(result.data["repositoryOrError"]["latestRunByStep"])

        assert result["asset_1"]["stepKey"] == "asset_1"
        assert result["asset_1"]["run"] == None

        # Test with 1 run on all assets
        first_run_id = _create_run(graphql_context, "failure_assets_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["repositoryOrError"]
        result = get_response_by_step(result.data["repositoryOrError"]["latestRunByStep"])
        assert result["asset_1"]["run"]["runId"] == first_run_id
        assert result["asset_2"]["run"]["runId"] == first_run_id
        assert result["asset_3"]["run"]["runId"] == first_run_id

        # Confirm that step selection is respected among 5 latest runs
        run_id = _create_run(graphql_context, "failure_assets_job", step_keys=["asset_3"])

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["repositoryOrError"]
        assert result.data["repositoryOrError"]["latestRunByStep"]
        result = get_response_by_step(result.data["repositoryOrError"]["latestRunByStep"])
        assert result["asset_1"]["run"]["runId"] == first_run_id
        assert result["asset_2"]["run"]["runId"] == first_run_id
        assert result["asset_3"]["run"]["runId"] == run_id

        # Create 4 runs
        # When 5 most recent runs in asset do not have asset selected, confirm that the number
        # of runs since last materialization is correct
        for _ in range(4):
            _create_run(graphql_context, "failure_assets_job", step_keys=["asset_3"])

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={"repositorySelector": selector},
        )

        assert result.data
        assert result.data["repositoryOrError"]
        result = get_response_by_step(result.data["repositoryOrError"]["latestRunByStep"])
        assert result["asset_1"]["jobNames"] == ["failure_assets_job"]
        # A job containing asset 1 was run 5 times, since latest materialization
        assert result["asset_1"]["count"] == 5
        assert result["asset_1"]["sinceLatestMaterialization"] == True
        # A job containing asset 2 was run 6 times, asset 2 was never materialized
        assert result["asset_2"]["count"] == 6
        assert result["asset_2"]["sinceLatestMaterialization"] == False


class TestPersistentInstanceAssetInProgress(ExecutingGraphQLContextTestMatrix):
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
