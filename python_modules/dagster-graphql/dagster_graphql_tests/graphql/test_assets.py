import datetime
import os
import time
from typing import Dict, List, Optional

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetSelection,
    DagsterEventType,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    Output,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    repository,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey
from dagster._core.test_utils import instance_for_test, poll_for_finished_run
from dagster._legacy import DagsterRunStatus
from dagster._utils import Counter, safe_tempfile_path, traced_counter
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_or_pipeline_selector,
    infer_pipeline_selector,
    infer_repository_selector,
)

# from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite
from dagster_graphql_tests.graphql.graphql_context_test_suite import (
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

GET_ASSET_DATA_VERSIONS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
        assetNodes(pipeline: $pipelineSelector, assetKeys: $assetKeys) {
            id
            assetKey {
              path
            }
            currentDataVersion
            staleStatus
            staleCauses {
                key { path }
                reason
                dependency { path }
            }
            assetMaterializations {
                tags {
                    key
                    value
                }
            }
        }
    }
"""


GET_ASSET_NODES_FROM_KEYS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
        assetNodes(pipeline: $pipelineSelector, assetKeys: $assetKeys) {
            id
            hasMaterializePermission
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

GET_PARTITIONS_BY_DIMENSION = """
    query AssetNodeQuery($assetKeys: [AssetKeyInput!], $startIdx: Int, $endIdx: Int) {
        assetNodes(assetKeys: $assetKeys) {
            id
            partitionKeysByDimension(startIdx: $startIdx, endIdx: $endIdx) {
                name
                partitionKeys
            }
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

GET_LATEST_RUN_FOR_PARTITION = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!, $partition: String!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            latestRunForPartition(partition: $partition) {
                runId
            }
        }
    }
"""


GET_MATERIALIZATION_USED_DATA = """
    query AssetNodeQuery($assetKey: AssetKeyInput!, $timestamp: String!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                id
                assetMaterializationUsedData(timestampMillis: $timestamp) {
                    __typename
                    timestamp
                    assetKey {
                        path
                    }
                    downstreamAssetKey {
                        path
                    }
                }
            }
        }
    }
"""

GET_FRESHNESS_INFO = """
    query AssetNodeQuery {
        assetNodes {
            id
            freshnessInfo {
                currentMinutesLate
                latestMaterializationMinutesLate
            }
            freshnessPolicy {
                cronSchedule
                maximumLagMinutes
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


GET_1D_ASSET_PARTITIONS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            assetPartitionStatuses {
                ... on TimePartitions {
                    ranges {
                        startTime
                        endTime
                        startKey
                        endKey
                        status
                    }
                }
                ... on DefaultPartitions {
                    materializedPartitions
                    failedPartitions
                    unmaterializedPartitions
                }
            }
            partitionKeysByDimension {
                partitionKeys
            }
            partitionDefinition {
                name
                timeWindowMetadata {
                    startTime
                    startKey
                }
            }
        }
    }
"""

GET_2D_ASSET_PARTITIONS = """
    query MaterializationStatusByDimension($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            assetPartitionStatuses {
                ... on MultiPartitions {
                    ranges {
                        primaryDimStartKey
                        primaryDimEndKey
                        primaryDimStartTime
                        primaryDimEndTime
                        secondaryDim {
                            ... on TimePartitions {
                                ranges {
                                    startTime
                                    endTime
                                    startKey
                                    endKey
                                    status
                                }
                            }
                            ... on DefaultPartitions {
                                materializedPartitions
                                failedPartitions
                                unmaterializedPartitions
                            }
                        }
                    }
                }
            }
        }
    }
"""

GET_PARTITION_STATS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            partitionStats {
                numMaterialized
                numPartitions
                numFailed
            }
        }
    }
"""

GET_MATERIALIZATION_FOR_DIMENSION_PARTITION = """
    query AssetGraphQuery($assetKey: AssetKeyInput!, $partitions: [String!], $tags: [InputTag!]) {
        assetOrError(assetKey: $assetKey) {
            ...on Asset{
                assetMaterializations(partitions: $partitions, tags: $tags) {
                    partition
                    runId
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

GET_ASSET_TYPE = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            assetKey {
                path
            }
            type {
                ..._DagsterTypeFragment
                innerTypes {
                ..._DagsterTypeFragment
                }
            }
        }
    }
    fragment _DagsterTypeFragment on DagsterType {
        key
        name
        displayName
    }
"""

BATCH_LOAD_ASSETS = """
    query BatchLoadQuery($assetKeys: [AssetKeyInput!]) {
        assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
            assetMaterializations(limit: 1) {
                timestamp
                runId
            }
        }
    }
"""


def _create_run(
    graphql_context, pipeline_name, mode="default", step_keys=None, asset_selection=None, tags=None
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
        variables={
            "executionParams": {
                "selector": selector,
                "mode": mode,
                "stepKeys": step_keys,
                "executionMetadata": {
                    "tags": tags if tags else [],
                },
            }
        },
    )
    assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
    run_id = result.data["launchPipelineExecution"]["run"]["runId"]
    poll_for_finished_run(graphql_context.instance, run_id)
    return run_id


def _create_partitioned_run(
    graphql_context,
    job_name: str,
    partition_key: str,
    asset_selection: Optional[List[AssetKey]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> str:
    partition_tags = [
        {"key": "dagster/partition", "value": partition_key},
    ]
    if isinstance(partition_key, MultiPartitionKey):
        partition_tags += [
            {"key": f"dagster/partition/{dimension_name}", "value": key}
            for dimension_name, key in partition_key.keys_by_dimension.items()
        ]
    return _create_run(
        graphql_context,
        job_name,
        asset_selection=[{"path": asset_key.path} for asset_key in asset_selection]
        if asset_selection
        else asset_selection,
        tags=[
            *partition_tags,
            {"key": "dagster/partition_set", "value": "multipartitions_job_partition_set"},
            *[{"key": k, "value": v} for k, v in (tags or {}).items()],
        ]
        + (
            [
                {
                    "key": "dagster/step_selection",
                    "value": ",".join([asset.path[-1] for asset in asset_selection]),
                }
            ]
            if asset_selection
            else []
        ),
    )


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
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["a"]}},
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
            variables={"assetKey": {"path": ["a"]}, "asOf": str(as_of_timestamp)},
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
            variables={"assetKey": {"path": ["a"]}, "afterTimestamp": str(after_timestamp)},
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
            variables={"assetKey": {"path": ["a"]}, "afterTimestamp": str(after_timestamp)},
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
            variables={
                "pipelineSelector": selector,
                "assetKeys": [{"path": ["asset_one"]}],
            },
        )

        assert result.data
        assert result.data["assetNodes"]

        assert len(result.data["assetNodes"]) == 1
        asset_node = result.data["assetNodes"][0]
        assert asset_node["id"] == 'test.test_repo.["asset_one"]'
        assert asset_node["hasMaterializePermission"]

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
        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="c")

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
        assert asset_node["latestMaterializationByPartition"][0] is None

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

        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="c")
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

        assert asset_node["latestMaterializationByPartition"][1] is None

    def test_latest_run_for_partition(self, graphql_context):
        run_id = _create_partitioned_run(
            graphql_context, "partition_materialization_job", partition_key="a"
        )

        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_RUN_FOR_PARTITION,
            variables={"pipelineSelector": selector, "partition": "a"},
        )
        assert result.data
        assert result.data["assetNodes"][0]["latestRunForPartition"]["runId"] == run_id

        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_RUN_FOR_PARTITION,
            variables={"pipelineSelector": selector, "partition": "b"},
        )
        assert result.data
        assert result.data["assetNodes"][0]["latestRunForPartition"] is None

    def test_materialization_used_data(self, graphql_context):
        def get_response_by_asset(response):
            return {stat["assetKey"]["path"][0]: stat for stat in response}

        _create_run(graphql_context, "two_assets_job")

        # Obtain the timestamp of the asset_one, asset_two materializations
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_LATEST_RUN_STATS,
            variables={"assetKeys": [{"path": ["asset_one"]}, {"path": ["asset_two"]}]},
        )

        assert result.data["assetsLatestInfo"]
        info = get_response_by_asset(result.data["assetsLatestInfo"])
        timestamp_a1 = info["asset_one"]["latestMaterialization"]["timestamp"]
        timestamp_a2 = info["asset_two"]["latestMaterialization"]["timestamp"]

        # Verify that the "used data" for asset_two matches the asset_one timestamp
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_USED_DATA,
            variables={"assetKey": {"path": ["asset_two"]}, "timestamp": timestamp_a2},
        )

        used_data = result.data["assetNodeOrError"]["assetMaterializationUsedData"]
        assert len(used_data) == 1
        assert used_data[0]["assetKey"]["path"] == ["asset_one"]
        assert used_data[0]["timestamp"] == timestamp_a1

    def test_default_partitions(self, graphql_context) -> None:
        # test for unpartitioned asset
        selector = infer_pipeline_selector(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]

        materialized_partitions = result.data["assetNodes"][0]["assetPartitionStatuses"][
            "materializedPartitions"
        ]
        assert len(materialized_partitions) == 0
        assert (
            len(result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"])
            == 0
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 2
        assert result.data["assetNodes"][0]["partitionStats"] is None
        assert result.data["assetNodes"][1]["partitionStats"] is None

        # Test for static partitioned asset with partitions [a, b, c, d]
        # First test that no partitions are materialized
        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]

        materialized_partitions = result.data["assetNodes"][0]["assetPartitionStatuses"][
            "materializedPartitions"
        ]
        assert len(materialized_partitions) == 0
        failed_partitons = result.data["assetNodes"][0]["assetPartitionStatuses"][
            "failedPartitions"
        ]
        assert len(failed_partitons) == 0
        assert (
            len(result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"])
            == 4
        )
        assert result.data["assetNodes"][0]["partitionDefinition"]["name"] is None

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 0
        assert result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4

        # Test that when partition a is materialized that the materialized partitions are a
        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="a")

        selector = infer_pipeline_selector(graphql_context, "partition_materialization_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialized_partitions = asset_node["assetPartitionStatuses"]["materializedPartitions"]
        assert len(materialized_partitions) == 1
        assert materialized_partitions[0] == "a"
        unmaterialized_partitions = asset_node["assetPartitionStatuses"]["unmaterializedPartitions"]
        assert len(unmaterialized_partitions) == 3
        assert set(unmaterialized_partitions) == {"b", "c", "d"}

        # Test that when partition c is materialized that the materialized partitions are a, c
        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="c")

        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialized_partitions = asset_node["assetPartitionStatuses"]["materializedPartitions"]
        assert len(materialized_partitions) == 2
        assert set(materialized_partitions) == {"a", "c"}
        unmaterialized_partitions = asset_node["assetPartitionStatuses"]["unmaterializedPartitions"]
        assert len(unmaterialized_partitions) == 2
        assert set(unmaterialized_partitions) == {"b", "d"}

    def test_partition_stats(self, graphql_context):
        _create_partitioned_run(
            graphql_context, "fail_partition_materialization_job", partition_key="b"
        )
        selector = infer_pipeline_selector(graphql_context, "fail_partition_materialization_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numFailed"] == 0

        _create_partitioned_run(
            graphql_context,
            "fail_partition_materialization_job",
            partition_key="a",
            tags={"fail": "true"},
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numFailed"] == 1

        # failing a partition that already materialized removes it from the numMaterialized count
        _create_partitioned_run(
            graphql_context,
            "fail_partition_materialization_job",
            partition_key="b",
            tags={"fail": "true"},
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 1
        assert result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 0
        assert result.data["assetNodes"][0]["partitionStats"]["numFailed"] == 2

    def test_dynamic_partitions(self, graphql_context):
        traced_counter.set(Counter())
        selector = infer_pipeline_selector(graphql_context, "dynamic_partitioned_assets_job")

        def _get_materialized_partitions():
            return execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": selector},
            )

        # No existing partitions
        result = _get_materialized_partitions()
        for i in range(2):
            materialized_partitions = result.data["assetNodes"][i]["assetPartitionStatuses"][
                "materializedPartitions"
            ]
            assert len(materialized_partitions) == 0
            assert (
                len(
                    result.data["assetNodes"][i]["assetPartitionStatuses"][
                        "unmaterializedPartitions"
                    ]
                )
                == 0
            )
            assert (
                result.data["assetNodes"][i]["partitionKeysByDimension"][0]["partitionKeys"] == []
            )

        counts = traced_counter.get().counts()
        assert counts.get("DagsterInstance.get_dynamic_partitions") == 1

        partitions = ["foo", "bar", "baz"]
        graphql_context.instance.add_dynamic_partitions("foo", partitions)

        result = _get_materialized_partitions()
        assert set(
            result.data["assetNodes"][0]["partitionKeysByDimension"][0]["partitionKeys"]
        ) == set(partitions)
        materialized_partitions = result.data["assetNodes"][0]["assetPartitionStatuses"][
            "materializedPartitions"
        ]
        assert result.data["assetNodes"][0]["partitionDefinition"]["name"] == "foo"
        assert result.data["assetNodes"][1]["partitionDefinition"]["name"] == "foo"
        assert len(materialized_partitions) == 0
        assert (
            len(result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"])
            == 3
        )
        assert set(
            result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"]
        ) == set(partitions)

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 0
        assert result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 3

    def test_time_partitions(self, graphql_context):
        def _get_datetime_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d-%H:%M")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test for hourly partitioned asset
        # First test that no partitions are materialized
        selector = infer_pipeline_selector(graphql_context, "time_partitioned_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]

        materialized_ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(materialized_ranges) == 0

        time_0 = "2021-07-05-00:00"
        time_1 = "2021-07-05-01:00"
        time_2 = "2021-07-05-02:00"
        time_3 = "2021-07-05-03:00"

        # Test that when partition a is materialized that the materialized partitions are a
        _create_partitioned_run(
            graphql_context, "time_partitioned_assets_job", partition_key=time_0
        )

        selector = infer_pipeline_selector(graphql_context, "time_partitioned_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialized_ranges = asset_node["assetPartitionStatuses"]["ranges"]

        assert len(materialized_ranges) == 1
        assert materialized_ranges[0]["startKey"] == time_0
        assert materialized_ranges[0]["endKey"] == time_0
        assert materialized_ranges[0]["startTime"] == _get_datetime_float(time_0)
        assert materialized_ranges[0]["endTime"] == _get_datetime_float(time_1)

        # Test that when partition 2021-07-05-02:00 is materialized that there are two materialized ranges
        time_2 = "2021-07-05-02:00"
        _create_partitioned_run(
            graphql_context, "time_partitioned_assets_job", partition_key=time_2
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialized_ranges = asset_node["assetPartitionStatuses"]["ranges"]

        assert len(materialized_ranges) == 2
        assert materialized_ranges[0]["startKey"] == time_0
        assert materialized_ranges[0]["endKey"] == time_0
        assert materialized_ranges[0]["startTime"] == _get_datetime_float(time_0)
        assert materialized_ranges[0]["endTime"] == _get_datetime_float(time_1)
        assert materialized_ranges[1]["startKey"] == time_2
        assert materialized_ranges[1]["endKey"] == time_2
        assert materialized_ranges[1]["startTime"] == _get_datetime_float(time_2)
        assert materialized_ranges[1]["endTime"] == _get_datetime_float(time_3)

        # Test that when partition 2021-07-05-01:00 is materialized that we have one range
        _create_partitioned_run(
            graphql_context, "time_partitioned_assets_job", partition_key=time_1
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_1D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        materialized_ranges = asset_node["assetPartitionStatuses"]["ranges"]

        assert len(materialized_ranges) == 1
        assert materialized_ranges[0]["startKey"] == time_0
        assert materialized_ranges[0]["endKey"] == time_2
        assert materialized_ranges[0]["startTime"] == _get_datetime_float(time_0)
        assert materialized_ranges[0]["endTime"] == _get_datetime_float(time_3)

        time_partitions_def_metadata = result.data["assetNodes"][0]["partitionDefinition"][
            "timeWindowMetadata"
        ]
        assert time_partitions_def_metadata is not None
        start_time = "2021-05-05-01:00"
        assert time_partitions_def_metadata["startTime"] == _get_datetime_float(start_time)
        assert time_partitions_def_metadata["startKey"] == start_time

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

        assert result["asset_1"]["latestRun"] is None
        assert result["asset_1"]["latestMaterialization"] is None

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
        assert result["asset_2"]["latestRun"]["id"] == first_run_id
        assert result["asset_2"]["latestMaterialization"] is None
        assert result["asset_3"]["latestRun"]["id"] == first_run_id
        assert result["asset_3"]["latestMaterialization"] is None

        # Confirm that asset selection is respected
        run_id = _create_run(
            graphql_context,
            "failure_assets_job",
            asset_selection=[{"path": ["asset_3"]}],
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
        assert result["asset_2"]["latestRun"]["id"] == first_run_id
        assert result["asset_3"]["latestRun"]["id"] == run_id

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
        assert run.status == DagsterRunStatus.SUCCESS
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
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["foo_bar"]}],
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
            asset_selection=[
                {"path": ["foo"]},
                {"path": ["bar"]},
                {"path": ["foo_bar"]},
            ],
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run.is_finished

        # Generate materializations with subselection of foo and baz
        run_id = _create_run(
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["baz"]}],
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

    def test_typed_assets(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "typed_assets")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_TYPE,
            variables={
                "pipelineSelector": selector,
            },
        )
        sorted_asset_nodes = sorted(result.data["assetNodes"], key=lambda x: x["assetKey"]["path"])
        assert sorted_asset_nodes[0]["assetKey"] == {"path": ["int_asset"]}
        assert sorted_asset_nodes[0]["type"]["displayName"] == "Int"
        assert sorted_asset_nodes[1]["assetKey"] == {"path": ["str_asset"]}
        assert sorted_asset_nodes[1]["type"]["displayName"] == "String"
        assert sorted_asset_nodes[2]["assetKey"] == {"path": ["typed_asset"]}
        assert sorted_asset_nodes[2]["type"]["displayName"] == "Int"
        assert sorted_asset_nodes[3]["assetKey"] == {"path": ["untyped_asset"]}
        assert sorted_asset_nodes[3]["type"]["displayName"] == "Any"

    def test_batch_fetch_only_once(self, graphql_context):
        traced_counter.set(Counter())
        result = execute_dagster_graphql(
            graphql_context,
            BATCH_LOAD_ASSETS,
            variables={
                "assetKeys": [{"path": ["int_asset"]}, {"path": ["str_asset"]}],
            },
        )
        assert result.data
        counts = traced_counter.get().counts()
        assert len(counts) == 1
        assert counts.get("DagsterInstance.get_asset_records") == 1

    def test_get_partitions_by_dimension(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITIONS_BY_DIMENSION,
            variables={
                "assetKeys": [{"path": ["multipartitions_1"]}],
            },
        )
        assert result.data
        dimensions = result.data["assetNodes"][0]["partitionKeysByDimension"]
        assert len(dimensions) == 2
        assert dimensions[0]["name"] == "ab"
        assert dimensions[0]["partitionKeys"] == ["a", "b", "c"]
        assert dimensions[1]["name"] == "date"
        assert dimensions[1]["partitionKeys"][0] == "2022-01-01"

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITIONS_BY_DIMENSION,
            variables={
                "assetKeys": [{"path": ["multipartitions_1"]}],
                "startIdx": 2,
                "endIdx": 3,
            },
        )
        assert result.data
        dimensions = result.data["assetNodes"][0]["partitionKeysByDimension"]
        assert len(dimensions) == 2
        assert dimensions[0]["name"] == "ab"
        assert dimensions[0]["partitionKeys"] == ["a", "b", "c"]
        assert dimensions[1]["name"] == "date"
        assert len(dimensions[1]["partitionKeys"]) == 1
        assert dimensions[1]["partitionKeys"][0] == "2022-01-03"

        result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITIONS_BY_DIMENSION,
            variables={
                "assetKeys": [{"path": ["upstream_time_partitioned_asset"]}],
                "startIdx": 2,
                "endIdx": 3,
            },
        )
        assert result.data
        dimensions = result.data["assetNodes"][0]["partitionKeysByDimension"]
        assert len(dimensions) == 1
        assert dimensions[0]["name"] == "default"
        assert len(dimensions[0]["partitionKeys"]) == 1
        assert dimensions[0]["partitionKeys"][0] == "2021-05-05-03:00"

    def test_multipartitions_get_materialization_status(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "no_multipartitions_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

    def test_multipartitions_get_status(self, graphql_context):
        def _get_date_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_pipeline_selector(graphql_context, "multipartitions_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []
        assert result.data["assetNodes"][1]["assetPartitionStatuses"]["ranges"] == []

        # Should generate three ranges:
        # 2022-01-01 has a and c materialized
        # 2022-01-03 has a and c materialized
        # 2022-01-04 has a materialized
        for partition_field in [
            ("2022-01-01", "a"),
            ("2022-01-01", "c"),
            ("2022-01-03", "a"),
            ("2022-01-03", "c"),
            ("2022-01-04", "a"),
        ]:
            _create_partitioned_run(
                graphql_context,
                "multipartitions_job",
                MultiPartitionKey({"date": partition_field[0], "ab": partition_field[1]}),
                asset_selection=[AssetKey("multipartitions_1")],
            )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 3
        # Both 2022-01-01 and 2022-01-03 should have a and c materialized
        for range_idx, date, end_date in [
            (0, "2022-01-01", "2022-01-02"),
            (1, "2022-01-03", "2022-01-04"),
        ]:
            assert ranges[range_idx]["primaryDimStartKey"] == date
            assert ranges[range_idx]["primaryDimEndKey"] == date
            assert ranges[range_idx]["primaryDimStartTime"] == _get_date_float(date)
            assert ranges[range_idx]["primaryDimEndTime"] == _get_date_float(end_date)
            assert len(ranges[range_idx]["secondaryDim"]["materializedPartitions"]) == 2
            assert set(ranges[range_idx]["secondaryDim"]["materializedPartitions"]) == set(
                ["a", "c"]
            )
            assert len(ranges[range_idx]["secondaryDim"]["failedPartitions"]) == 0
        # 2022-01-04 should only have a materialized
        assert ranges[2]["primaryDimStartKey"] == "2022-01-04"
        assert ranges[2]["primaryDimEndKey"] == "2022-01-04"
        assert len(ranges[2]["secondaryDim"]["materializedPartitions"]) == 1
        assert ranges[2]["secondaryDim"]["materializedPartitions"][0] == "a"
        # multipartitions_2 should have no materialized partitions
        assert result.data["assetNodes"][1]["assetPartitionStatuses"]["ranges"] == []

        # After materializing the below partitions, multipartitions_1 should have 2 ranges:
        # 2022-01-01...2022-01-03 has a...c materialized
        # 2022-01-04 has a...b materialized
        for partition_field in [
            ("2022-01-01", "b"),
            ("2022-01-03", "b"),
            ("2022-01-02", "a"),
            ("2022-01-02", "b"),
            ("2022-01-02", "c"),
            ("2022-01-04", "b"),
        ]:
            _create_partitioned_run(
                graphql_context,
                "multipartitions_job",
                MultiPartitionKey({"date": partition_field[0], "ab": partition_field[1]}),
                asset_selection=[AssetKey("multipartitions_1")],
            )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 2
        # 2022-01-01...2022-01-03 should have a...c materialized
        assert ranges[0]["primaryDimStartKey"] == "2022-01-01"
        assert ranges[0]["primaryDimEndKey"] == "2022-01-03"
        assert ranges[0]["primaryDimStartTime"] == _get_date_float("2022-01-01")
        assert ranges[0]["primaryDimEndTime"] == _get_date_float("2022-01-04")
        assert len(ranges[0]["secondaryDim"]["materializedPartitions"]) == 3
        assert set(ranges[0]["secondaryDim"]["materializedPartitions"]) == set(["a", "b", "c"])
        assert len(ranges[0]["secondaryDim"]["failedPartitions"]) == 0
        # 2022-01-04 should have a...b materialized
        assert ranges[1]["primaryDimStartKey"] == "2022-01-04"
        assert ranges[1]["primaryDimEndKey"] == "2022-01-04"
        assert ranges[1]["primaryDimStartTime"] == _get_date_float("2022-01-04")
        assert ranges[1]["primaryDimEndTime"] == _get_date_float("2022-01-05")
        assert len(ranges[1]["secondaryDim"]["materializedPartitions"]) == 2
        assert set(ranges[1]["secondaryDim"]["materializedPartitions"]) == set(["a", "b"])
        assert len(ranges[1]["secondaryDim"]["failedPartitions"]) == 0
        # multipartitions_2 should have no materialized partitions
        assert result.data["assetNodes"][1]["assetPartitionStatuses"]["ranges"] == []

    def test_multipartitions_get_failed_status(self, graphql_context):
        def _get_date_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_pipeline_selector(graphql_context, "multipartitions_fail_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

        # Should generate three ranges:
        # 2022-01-01 has a and c failed
        # 2022-01-03 has a and c failed
        # 2022-01-04 has a failed
        for partition_field in [
            ("2022-01-01", "a"),
            ("2022-01-01", "c"),
            ("2022-01-03", "a"),
            ("2022-01-03", "c"),
            ("2022-01-04", "a"),
        ]:
            _create_partitioned_run(
                graphql_context,
                "multipartitions_fail_job",
                MultiPartitionKey({"date": partition_field[0], "ab": partition_field[1]}),
                tags={"fail": "true"},
            )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 3
        # Both 2022-01-01 and 2022-01-03 should have a and c failed
        for range_idx, date, end_date in [
            (0, "2022-01-01", "2022-01-02"),
            (1, "2022-01-03", "2022-01-04"),
        ]:
            assert ranges[range_idx]["primaryDimStartKey"] == date
            assert ranges[range_idx]["primaryDimEndKey"] == date
            assert ranges[range_idx]["primaryDimStartTime"] == _get_date_float(date)
            assert ranges[range_idx]["primaryDimEndTime"] == _get_date_float(end_date)
            assert len(ranges[range_idx]["secondaryDim"]["failedPartitions"]) == 2
            assert set(ranges[range_idx]["secondaryDim"]["failedPartitions"]) == set(["a", "c"])
            assert len(ranges[range_idx]["secondaryDim"]["materializedPartitions"]) == 0
        # 2022-01-04 should only have a failed
        assert ranges[2]["primaryDimStartKey"] == "2022-01-04"
        assert ranges[2]["primaryDimEndKey"] == "2022-01-04"
        assert len(ranges[2]["secondaryDim"]["failedPartitions"]) == 1
        assert ranges[2]["secondaryDim"]["failedPartitions"][0] == "a"

        # After failing the below partitions, should have 2 ranges:
        # 2022-01-01...2022-01-03 has a...c failed
        # 2022-01-04 has a...b failed
        for partition_field in [
            ("2022-01-01", "b"),
            ("2022-01-03", "b"),
            ("2022-01-02", "a"),
            ("2022-01-02", "b"),
            ("2022-01-02", "c"),
            ("2022-01-04", "b"),
        ]:
            _create_partitioned_run(
                graphql_context,
                "multipartitions_fail_job",
                MultiPartitionKey({"date": partition_field[0], "ab": partition_field[1]}),
                tags={"fail": "true"},
            )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 2
        # 2022-01-01...2022-01-03 should have a...c failed
        assert ranges[0]["primaryDimStartKey"] == "2022-01-01"
        assert ranges[0]["primaryDimEndKey"] == "2022-01-03"
        assert ranges[0]["primaryDimStartTime"] == _get_date_float("2022-01-01")
        assert ranges[0]["primaryDimEndTime"] == _get_date_float("2022-01-04")
        assert len(ranges[0]["secondaryDim"]["failedPartitions"]) == 3
        assert set(ranges[0]["secondaryDim"]["failedPartitions"]) == set(["a", "b", "c"])
        assert len(ranges[0]["secondaryDim"]["materializedPartitions"]) == 0

        # Materialize some failed partitions
        for partition_field in [
            ("2022-01-01", "b"),
            ("2022-01-02", "b"),
            ("2022-01-03", "b"),
        ]:
            _create_partitioned_run(
                graphql_context,
                "multipartitions_fail_job",
                MultiPartitionKey({"date": partition_field[0], "ab": partition_field[1]}),
            )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 2
        assert ranges[0]["primaryDimStartKey"] == "2022-01-01"
        assert ranges[0]["primaryDimEndKey"] == "2022-01-03"
        assert ranges[0]["primaryDimStartTime"] == _get_date_float("2022-01-01")
        assert ranges[0]["primaryDimEndTime"] == _get_date_float("2022-01-04")
        assert set(ranges[0]["secondaryDim"]["failedPartitions"]) == set(["a", "c"])
        assert set(ranges[0]["secondaryDim"]["materializedPartitions"]) == set(["b"])

    def test_dynamic_dim_in_multipartitions_def(self, graphql_context):
        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_pipeline_selector(
            graphql_context, "dynamic_in_multipartitions_success_job"
        )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

        graphql_context.instance.add_dynamic_partitions("dynamic", ["1", "2", "3"])

        # static = a, dynamic = 1
        # succeeded in dynamic_in_multipartitions_success asset,
        # failed in dynamic_in_multipartitions_fail asset
        _create_partitioned_run(
            graphql_context,
            "dynamic_in_multipartitions_success_job",
            MultiPartitionKey({"dynamic": "1", "static": "a"}),
        )
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]

        # success asset contains 1 materialized range
        success_asset_result = result.data["assetNodes"][1]
        assert "dynamic_in_multipartitions_success" in success_asset_result["id"]
        ranges = success_asset_result["assetPartitionStatuses"]["ranges"]
        ranges = result.data["assetNodes"][1]["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 1
        assert ranges[0]["primaryDimStartKey"] == "1"
        assert ranges[0]["primaryDimEndKey"] == "1"
        assert len(ranges[0]["secondaryDim"]["failedPartitions"]) == 0
        assert len(ranges[0]["secondaryDim"]["materializedPartitions"]) == 1
        assert ranges[0]["secondaryDim"]["materializedPartitions"] == ["a"]

        # failed asset contains 1 failed range
        fail_asset_result = result.data["assetNodes"][0]
        assert "dynamic_in_multipartitions_fail" in fail_asset_result["id"]
        ranges = fail_asset_result["assetPartitionStatuses"]["ranges"]
        assert len(ranges) == 1
        assert ranges[0]["primaryDimStartKey"] == "1"
        assert ranges[0]["primaryDimEndKey"] == "1"
        assert len(ranges[0]["secondaryDim"]["failedPartitions"]) == 1
        assert ranges[0]["secondaryDim"]["failedPartitions"] == ["a"]
        assert len(ranges[0]["secondaryDim"]["materializedPartitions"]) == 0

    def test_get_materialization_for_multipartition(self, graphql_context):
        first_run_id = _create_partitioned_run(
            graphql_context,
            "multipartitions_job",
            MultiPartitionKey({"date": "2022-01-01", "ab": "a"}),
            [AssetKey("multipartitions_1")],
        )
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_FOR_DIMENSION_PARTITION,
            variables={
                "assetKey": {"path": ["multipartitions_1"]},
                "tags": [{"name": "dagster/partition/ab", "value": "a"}],
            },
        )
        assert result.data
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 1
        assert materializations[0]["partition"] == "a|2022-01-01"
        assert materializations[0]["runId"] == first_run_id

        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_FOR_DIMENSION_PARTITION,
            variables={
                "assetKey": {"path": ["multipartitions_2"]},
                "tags": [{"name": "dagster/partition/ab", "value": "a"}],
            },
        )
        materializations = result.data["assetOrError"]["assetMaterializations"]
        assert len(materializations) == 0

        second_run_id = _create_partitioned_run(
            graphql_context,
            "multipartitions_job",
            MultiPartitionKey({"ab": "b", "date": "2022-01-01"}),
            [AssetKey("multipartitions_1")],
        )
        result = execute_dagster_graphql(
            graphql_context,
            GET_MATERIALIZATION_FOR_DIMENSION_PARTITION,
            variables={
                "assetKey": {"path": ["multipartitions_1"]},
                "tags": [{"name": "dagster/partition/ab", "value": "b"}],
            },
        )
        assert result.data
        materializations = result.data["assetOrError"]["assetMaterializations"]
        # Should only fetch materializations where dimension "ab" partition is "b"
        assert len(materializations) == 1
        assert materializations[0]["partition"] == "b|2022-01-01"
        assert materializations[0]["runId"] == second_run_id

    def test_freshness_info(self, graphql_context, snapshot):
        _create_run(graphql_context, "fresh_diamond_assets")
        result = execute_dagster_graphql(graphql_context, GET_FRESHNESS_INFO)

        assert result.data
        assert result.data["assetNodes"]

        snapshot.assert_match(result.data)


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
            assert assets_live_info[1]["latestMaterialization"] is None
            assert assets_live_info[1]["unstartedRunIds"] == []
            assert assets_live_info[1]["inProgressRunIds"] == [run_id]

            assert assets_live_info[2]["assetKey"]["path"] == ["never_runs_asset"]
            assert assets_live_info[2]["latestMaterialization"] is None
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
            assert assets_live_info[1]["latestMaterialization"] is None
            assert assets_live_info[1]["unstartedRunIds"] == []
            assert assets_live_info[1]["inProgressRunIds"] == [run_id]

            assert assets_live_info[0]["assetKey"]["path"] == ["downstream_asset"]
            assert assets_live_info[0]["latestMaterialization"] is None
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
            graphql_context,
            CROSS_REPO_ASSET_GRAPH,
            variables={"repositorySelector": selector},
        )
        asset_nodes = result.data["assetNodes"]
        upstream_asset = [
            node
            for node in asset_nodes
            if node["id"] == 'cross_asset_repos.upstream_assets_repository.["upstream_asset"]'
        ][0]
        dependent_asset_keys = [
            {"path": ["downstream_asset1"]},
            {"path": ["downstream_asset2"]},
        ]

        result_dependent_keys = sorted(
            upstream_asset["dependedByKeys"], key=lambda node: node.get("path")[0]
        )
        assert result_dependent_keys == dependent_asset_keys


def get_partitioned_asset_repo():
    static_partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=static_partitions_def)
    def abc_asset(_):
        yield AssetMaterialization(asset_key="abc_asset", partition="invalid_partition_key")
        yield Output(5)

    daily_partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=daily_partitions_def)
    def daily_asset(_):
        # invalid partition key
        yield AssetMaterialization(asset_key="daily_asset", partition="2021-01-01")
        yield Output(5)

    multipartitions_def = MultiPartitionsDefinition(
        {
            "abcd": static_partitions_def,
            "date": daily_partitions_def,
        }
    )

    @asset(partitions_def=multipartitions_def)
    def multipartitions_asset(_):
        return 1

    @repository
    def partitioned_asset_repo():
        return [
            abc_asset,
            define_asset_job("abc_asset_job", AssetSelection.keys("abc_asset")),
            daily_asset,
            define_asset_job("daily_asset_job", AssetSelection.keys("daily_asset")),
            multipartitions_asset,
            define_asset_job(
                "multipartitions_job",
                AssetSelection.keys("multipartitions_asset"),
                partitions_def=multipartitions_def,
            ),
        ]

    return partitioned_asset_repo


def test_1d_subset_backcompat():
    with instance_for_test() as instance:
        instance.can_cache_asset_status_data = lambda: False
        assert instance.can_cache_asset_status_data() is False

        with define_out_of_process_context(
            __file__, "get_partitioned_asset_repo", instance
        ) as graphql_context:
            abc_selector = infer_pipeline_selector(graphql_context, "abc_asset_job")
            result = execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": abc_selector},
            )
            assert result.data
            assert len(result.data["assetNodes"]) == 1
            assert (
                result.data["assetNodes"][0]["assetPartitionStatuses"]["materializedPartitions"]
                == []
            )
            assert set(
                result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"]
            ) == {"a", "b", "c", "d"}

            for partition in ["a", "c", "d"]:
                _create_partitioned_run(graphql_context, "abc_asset_job", partition)

            result = execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": abc_selector},
            )
            assert result.data
            assert set(
                result.data["assetNodes"][0]["assetPartitionStatuses"]["materializedPartitions"]
            ) == {
                "a",
                "c",
                "d",
            }
            assert set(
                result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"]
            ) == {
                "b",
            }

            daily_job_selector = infer_pipeline_selector(graphql_context, "daily_asset_job")
            result = execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": daily_job_selector},
            )
            assert result.data
            assert len(result.data["assetNodes"]) == 1
            assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

            for partition in ["2022-03-03", "2022-03-05", "2022-03-06"]:
                _create_partitioned_run(graphql_context, "daily_asset_job", partition)

            result = execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": daily_job_selector},
            )
            assert result.data
            ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
            assert len(ranges) == 2
            assert ranges[0]["startKey"] == "2022-03-03"
            assert ranges[0]["endKey"] == "2022-03-03"
            assert ranges[1]["startKey"] == "2022-03-05"
            assert ranges[1]["endKey"] == "2022-03-06"

            result = execute_dagster_graphql(
                graphql_context,
                GET_PARTITION_STATS,
                variables={"pipelineSelector": daily_job_selector},
            )
            assert result.data
            assert result.data["assetNodes"]
            assert len(result.data["assetNodes"]) == 1
            assert result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 3


def test_2d_subset_backcompat():
    with instance_for_test() as instance:
        instance.can_cache_asset_status_data = lambda: False
        assert instance.can_cache_asset_status_data() is False

        with define_out_of_process_context(
            __file__, "get_partitioned_asset_repo", instance
        ) as graphql_context:
            multipartitions_selector = infer_pipeline_selector(
                graphql_context, "multipartitions_job"
            )
            result = execute_dagster_graphql(
                graphql_context,
                GET_2D_ASSET_PARTITIONS,
                variables={"pipelineSelector": multipartitions_selector},
            )
            assert result.data
            assert len(result.data["assetNodes"]) == 1
            assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

            for partition_fields in [
                ("2022-03-03", "a"),
                ("2022-03-03", "c"),
                ("2022-03-04", "a"),
                ("2022-03-04", "c"),
                ("2022-03-06", "a"),
                ("2022-03-06", "c"),
            ]:
                partition_key = MultiPartitionKey(
                    {"date": partition_fields[0], "abcd": partition_fields[1]}
                )
                _create_partitioned_run(graphql_context, "multipartitions_job", partition_key)

            result = execute_dagster_graphql(
                graphql_context,
                GET_2D_ASSET_PARTITIONS,
                variables={"pipelineSelector": multipartitions_selector},
            )

            ranges = result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"]
            assert len(ranges) == 2

            assert ranges[0]["primaryDimStartKey"] == "2022-03-03"
            assert ranges[0]["primaryDimEndKey"] == "2022-03-04"
            assert set(ranges[0]["secondaryDim"]["materializedPartitions"]) == {"a", "c"}
            assert set(ranges[0]["secondaryDim"]["unmaterializedPartitions"]) == {"b", "d"}

            assert ranges[1]["primaryDimStartKey"] == "2022-03-06"
            assert ranges[1]["primaryDimEndKey"] == "2022-03-06"
            assert len(ranges[1]["secondaryDim"]["materializedPartitions"]) == 2
            assert set(ranges[1]["secondaryDim"]["materializedPartitions"]) == {"a", "c"}
            assert set(ranges[1]["secondaryDim"]["unmaterializedPartitions"]) == {"b", "d"}
