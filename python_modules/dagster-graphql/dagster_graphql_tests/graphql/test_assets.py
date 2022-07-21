import os
import time

from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_job_or_pipeline_selector,
    infer_pipeline_selector,
    infer_repository_selector,
)

from dagster import AssetKey, DagsterEventType, PipelineRunStatus
from dagster._utils import safe_tempfile_path
from dagster._core.test_utils import poll_for_finished_run

# from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite
from .graphql_context_test_suite import (
    AllRepositoryGraphQLContextTestMatrix,
    ExecutingGraphQLContextTestMatrix,
)

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
    query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
        assetsLatestInfo(assetKeys: $assetKeys) {
            assetKey {
                path
            }
            latestMaterialization {
                timestamp
                runId
            }
            unstartedRunIds
            inProgressRunIds
        }
    }
"""


GET_ASSET_LATEST_RUN_STATS = """
    query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
        assetsLatestInfo(assetKeys: $assetKeys) {
            assetKey {
                path
            }
            computeStatus
            latestMaterialization {
                timestamp
                runId
            }
            latestRun {
                status
                id
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

CROSS_REPO_ASSET_GRAPH = """
    query AssetNodeQuery {
        assetNodes {
            id
            dependencyKeys {
                path
            }
            dependedByKeys {
                path
            }
        }
    }
"""

GET_REPO_ASSET_GROUPS = """
    query($repositorySelector: RepositorySelector!) {
        repositoryOrError(repositorySelector:$repositorySelector) {
            ... on Repository {
                assetGroups {
                    groupName
                    assetKeys {
                    path
                    }
                }
            }
        }
    }
"""


GET_RUN_MATERIALIZATIONS = """
    query RunAssetsQuery {
        runsOrError {
            ... on Runs {
                results {
                    assetMaterializations {
                        assetKey {
                            path
                        }
                    }
                }
            }
        }
    }
"""


def _create_run(
    graphql_context, pipeline_name, mode="default", step_keys=None, asset_selection=None
):
    if asset_selection:
        selector = infer_job_or_pipeline_selector(
            graphql_context, pipeline_name, asset_selection=asset_selection
        )
    else:
        selector = infer_pipeline_selector(
            graphql_context,
            pipeline_name,
        )
    result = execute_dagster_graphql(
        graphql_context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={"executionParams": {"selector": selector, "mode": mode, "stepKeys": step_keys}},
    )
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    run_id = result.data["launchPipelineExecution"]["run"]["runId"]
    poll_for_finished_run(graphql_context.instance, run_id)
    return run_id


def _get_sorted_materialization_events(graphql_context, run_id):
    return sorted(
        [
            event
            for event in graphql_context.instance.all_logs(run_id=run_id)
            if event.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION
        ],
        key=lambda event: event.get_dagster_event().asset_key,
    )


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
        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        poll_for_finished_run(graphql_context.instance, run_id)

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
        run_id = result.data["launchPipelineExecution"]["run"]["runId"]
        poll_for_finished_run(graphql_context.instance, run_id)

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
        assert asset_node["id"] == 'test.test_repo.["asset_one"]'

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]

        assert len(result.data["assetNodes"]) == 2
        asset_node = result.data["assetNodes"][0]
        assert asset_node["id"] == 'test.test_repo.["asset_one"]'

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

    def test_latest_run_by_asset(self, graphql_context):
        def get_response_by_asset(response):
            return {stat["assetKey"]["path"][0]: stat for stat in response}

        # Confirm that when no runs are present, run returned is None
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={
                "assetKeys": [
                    {"path": "asset_1"},
                    {"path": "asset_2"},
                    {"path": "asset_3"},
                ]
            },
        )

        assert result.data
        assert result.data["assetsLatestInfo"]
        result = get_response_by_asset(result.data["assetsLatestInfo"])

        assert result["asset_1"]["latestRun"] == None
        assert result["asset_1"]["latestMaterialization"] == None
        assert result["asset_1"]["computeStatus"] == "NONE"

        # Test with 1 run on all assets
        first_run_id = _create_run(graphql_context, "failure_assets_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={
                "assetKeys": [
                    {"path": "asset_1"},
                    {"path": "asset_2"},
                    {"path": "asset_3"},
                ]
            },
        )

        assert result.data
        assert result.data["assetsLatestInfo"]
        result = get_response_by_asset(result.data["assetsLatestInfo"])

        assert result["asset_1"]["latestRun"]["id"] == first_run_id
        assert result["asset_1"]["latestMaterialization"]["runId"] == first_run_id
        assert result["asset_1"]["computeStatus"] == "UP_TO_DATE"
        assert result["asset_2"]["latestRun"]["id"] == first_run_id
        assert result["asset_2"]["latestMaterialization"] == None
        assert result["asset_2"]["computeStatus"] == "NONE"
        assert result["asset_3"]["latestRun"]["id"] == first_run_id
        assert result["asset_3"]["latestMaterialization"] == None
        assert result["asset_3"]["computeStatus"] == "NONE"

        # Confirm that asset selection is respected
        run_id = _create_run(
            graphql_context, "failure_assets_job", asset_selection=[{"path": ["asset_3"]}]
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={
                "assetKeys": [
                    {"path": "asset_1"},
                    {"path": "asset_2"},
                    {"path": "asset_3"},
                ]
            },
        )

        assert result.data
        assert result.data["assetsLatestInfo"]
        result = get_response_by_asset(result.data["assetsLatestInfo"])
        assert result["asset_1"]["latestRun"]["id"] == first_run_id
        assert result["asset_1"]["computeStatus"] == "UP_TO_DATE"
        assert result["asset_2"]["latestRun"]["id"] == first_run_id
        assert result["asset_2"]["computeStatus"] == "NONE"
        assert result["asset_3"]["latestRun"]["id"] == run_id
        assert result["asset_3"]["computeStatus"] == "OUT_OF_DATE"

    def test_get_run_materialization(self, graphql_context, snapshot):
        _create_run(graphql_context, "single_asset_pipeline")
        result = execute_dagster_graphql(graphql_context, GET_RUN_MATERIALIZATIONS)
        assert result.data
        assert result.data["runsOrError"]
        assert result.data["runsOrError"]["results"]
        assert len(result.data["runsOrError"]["results"]) == 1
        assert len(result.data["runsOrError"]["results"][0]["assetMaterializations"]) == 1
        snapshot.assert_match(result.data)

    def test_asset_selection_in_run(self, graphql_context):
        # Generate materializations for bar asset
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        assert run.status == PipelineRunStatus.SUCCESS
        assert run.asset_selection == {AssetKey("bar")}

    def test_execute_pipeline_subset(self, graphql_context):
        # Assets foo and bar are upstream dependencies of asset foo_bar

        # Execute subselection with asset bar
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 1
        assert events[0].get_dagster_event().asset_key == AssetKey("bar")

        # Execute subselection with assets foo and foo_bar
        run_id = _create_run(
            graphql_context, "foo_job", asset_selection=[{"path": ["foo"]}, {"path": ["foo_bar"]}]
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("foo")
        assert events[1].get_dagster_event().asset_key == AssetKey("foo_bar")

    def test_execute_dependent_subset(self, graphql_context):
        # Asset foo is upstream of baz but not directly connected

        # Generate materializations for all assets upstream of baz
        run_id = _create_run(
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["bar"]}, {"path": ["foo_bar"]}],
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished

        # Generate materializations with subselection of foo and baz
        run_id = _create_run(
            graphql_context, "foo_job", asset_selection=[{"path": ["foo"]}, {"path": ["baz"]}]
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("baz")
        assert events[1].get_dagster_event().asset_key == AssetKey("foo")

    def test_execute_unconnected_subset(self, graphql_context):
        # Assets "foo" and "unconnected" are disconnected assets
        run_id = _create_run(
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["unconnected"]}],
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("foo")
        assert events[1].get_dagster_event().asset_key == AssetKey("unconnected")

    def test_reexecute_subset(self, graphql_context):
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 1
        assert events[0].get_dagster_event().asset_key == AssetKey("bar")
        assert run.asset_selection == {AssetKey("bar")}

        selector = infer_job_or_pipeline_selector(
            graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}]
        )
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "executionMetadata": {"parentRunId": run_id, "rootRunId": run_id},
                },
            },
        )
        run_id = result.data["launchPipelineReexecution"]["run"]["runId"]
        poll_for_finished_run(graphql_context.instance, run_id)

        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 1
        assert events[0].get_dagster_event().asset_key == AssetKey("bar")
        assert run.asset_selection == {AssetKey("bar")}

    def test_named_groups(self, graphql_context):
        _create_run(graphql_context, "named_groups_job")
        selector = {
            "repositoryLocationName": "test",
            "repositoryName": "test_repo",
        }

        result = execute_dagster_graphql(
            graphql_context,
            GET_REPO_ASSET_GROUPS,
            variables={
                "repositorySelector": selector,
            },
        )

        asset_groups_list = result.data["repositoryOrError"]["assetGroups"]
        # normalize for easy comparison
        asset_groups_dict = {
            group["groupName"]: sorted(".".join(key["path"]) for key in group["assetKeys"])
            for group in asset_groups_list
        }
        # The default group accumulates a lot of asset keys from other test data so we
        # compare it separately
        default_group_members = set(asset_groups_dict.pop("default"))

        expected_asset_groups = [
            ("group_1", ["grouped_asset_1", "grouped_asset_2"]),
            ("group_2", ["grouped_asset_4"]),
        ]
        assert sorted(asset_groups_dict.items()) == expected_asset_groups

        expected_default_group_members = {"ungrouped_asset_3", "ungrouped_asset_5"}
        assert (
            expected_default_group_members & default_group_members
        ) == expected_default_group_members


class TestPersistentInstanceAssetInProgress(ExecutingGraphQLContextTestMatrix):
    def test_asset_in_progress(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "hanging_job")

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
                    }
                },
            )

            assert not result.errors
            assert result.data

            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context,
                GET_ASSET_IN_PROGRESS_RUNS,
                variables={
                    "assetKeys": [
                        {"path": "first_asset"},
                        {"path": "hanging_asset"},
                        {"path": "never_runs_asset"},
                    ]
                },
            )
            graphql_context.instance.run_launcher.terminate(run_id)

            assert result.data
            assert result.data["assetsLatestInfo"]

            assets_live_info = result.data["assetsLatestInfo"]

            assets_live_info = sorted(assets_live_info, key=lambda res: res["assetKey"]["path"])
            assert len(assets_live_info) == 3

            assert assets_live_info[0]["assetKey"]["path"] == ["first_asset"]
            assert assets_live_info[0]["latestMaterialization"]["runId"] == run_id
            assert assets_live_info[0]["unstartedRunIds"] == []
            assert assets_live_info[0]["inProgressRunIds"] == []

            assert assets_live_info[1]["assetKey"]["path"] == ["hanging_asset"]
            assert assets_live_info[1]["latestMaterialization"] == None
            assert assets_live_info[1]["unstartedRunIds"] == []
            assert assets_live_info[1]["inProgressRunIds"] == [run_id]

            assert assets_live_info[2]["assetKey"]["path"] == ["never_runs_asset"]
            assert assets_live_info[2]["latestMaterialization"] == None
            assert assets_live_info[2]["unstartedRunIds"] == [run_id]
            assert assets_live_info[2]["inProgressRunIds"] == []

    def test_graph_asset_in_progress(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "hanging_graph_asset_job")

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
                    }
                },
            )

            assert not result.errors
            assert result.data

            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context,
                GET_ASSET_IN_PROGRESS_RUNS,
                variables={
                    "assetKeys": [
                        {"path": "hanging_graph"},
                        {"path": "downstream_asset"},
                    ]
                },
            )
            graphql_context.instance.run_launcher.terminate(run_id)

            assert result.data
            assert result.data["assetsLatestInfo"]

            assets_live_info = result.data["assetsLatestInfo"]

            assets_live_info = sorted(assets_live_info, key=lambda res: res["assetKey"]["path"])
            assert len(assets_live_info) == 2

            assert assets_live_info[1]["assetKey"]["path"] == ["hanging_graph"]
            assert assets_live_info[1]["latestMaterialization"] == None
            assert assets_live_info[1]["unstartedRunIds"] == []
            assert assets_live_info[1]["inProgressRunIds"] == [run_id]

            assert assets_live_info[0]["assetKey"]["path"] == ["downstream_asset"]
            assert assets_live_info[0]["latestMaterialization"] == None
            assert assets_live_info[0]["unstartedRunIds"] == [run_id]
            assert assets_live_info[0]["inProgressRunIds"] == []


class TestCrossRepoAssetDependedBy(AllRepositoryGraphQLContextTestMatrix):
    def test_cross_repo_assets(self, graphql_context):
        repository_location = graphql_context.get_repository_location("cross_asset_repos")
        repository = repository_location.get_repository("upstream_assets_repository")

        selector = {
            "repositoryLocationName": repository_location.name,
            "repositoryName": repository.name,
        }
        result = execute_dagster_graphql(
            graphql_context, CROSS_REPO_ASSET_GRAPH, variables={"repositorySelector": selector}
        )
        asset_nodes = result.data["assetNodes"]
        upstream_asset = [
            node
            for node in asset_nodes
            if node["id"] == 'cross_asset_repos.upstream_assets_repository.["upstream_asset"]'
        ][0]
        dependent_asset_keys = [{"path": ["downstream_asset1"]}, {"path": ["downstream_asset2"]}]

        result_dependent_keys = sorted(
            upstream_asset["dependedByKeys"], key=lambda node: node.get("path")[0]
        )
        assert result_dependent_keys == dependent_asset_keys
