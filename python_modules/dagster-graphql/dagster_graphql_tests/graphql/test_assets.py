import datetime
import json
import os
import time
from typing import Dict, List, Optional, Sequence

import pytest
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
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import instance_for_test, poll_for_finished_run
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import Counter, safe_tempfile_path, traced_counter
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.implementation.execution.run_lifecycle import create_valid_pipeline_run
from dagster_graphql.implementation.utils import ExecutionParams, pipeline_selector_from_graphql
from dagster_graphql.schema.roots.mutation import create_execution_metadata
from dagster_graphql.test.utils import (
    GqlAssetKey,
    GqlTag,
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_selector,
    infer_repository_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    AllRepositoryGraphQLContextTestMatrix,
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)

GET_ASSETS_QUERY = """
    query AssetKeyQuery($cursor: String, $limit: Int) {
        assetsOrError(cursor: $cursor, limit: $limit) {
            __typename
            ...on AssetConnection {
                nodes {
                    id
                    key {
                        path
                    }
                }
                cursor
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
    mutation AssetKeyWipe($assetPartitionRanges: [PartitionsByAssetSelector!]!) {
        wipeAssets(assetPartitionRanges: $assetPartitionRanges) {
            __typename
            ... on UnsupportedOperationError {
              message
            }
            ... on AssetNotFoundError {
              message
            }
            ... on AssetWipeSuccess {
                assetPartitionRanges {
                    assetKey {
                        path
                    }
                    partitionRange {
                        start
                        end
                    }
                }
            }
        }
    }
"""

REPORT_RUNLESS_ASSET_EVENTS = """
mutation reportRunlessAssetEvents($eventParams: ReportRunlessAssetEventsParams!) {
	reportRunlessAssetEvents(eventParams: $eventParams) {
    __typename
    ... on PythonError {
      message
      stack
    }
    ... on ReportRunlessAssetEventsSuccess {
      assetKey {
        path
      }
    }
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
            dataVersion
            staleStatus
            staleCauses {
                key { path }
                category
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

GET_ASSET_DATA_VERSIONS_BY_PARTITION = """
    query AssetNodeQuery($assetKey: AssetKeyInput!, $partition: String, $partitions: [String!]) {
        assetNodeOrError(assetKey: $assetKey) {
            ... on AssetNode {
                id
                assetKey {
                  path
                }
                dataVersion(partition: $partition)
                dataVersionByPartition(partitions: $partitions)
                staleStatus(partition: $partition)
                staleCauses(partition: $partition) {
                    key { path }
                    partitionKey
                    category
                    reason
                    dependency { path }
                    dependencyPartitionKey
                }
                staleStatusByPartition(partitions: $partitions)
                staleCausesByPartition(partitions: $partitions) {
                    key { path }
                    partitionKey
                    category
                    reason
                    dependency { path }
                    dependencyPartitionKey
                }
                assetMaterializations {
                    tags {
                        key
                        value
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
            hasMaterializePermission
            hasReportRunlessAssetEventPermission
        }
    }
"""

GET_ASSET_IS_EXECUTABLE = """
    query AssetNodeQuery($assetKeys: [AssetKeyInput!]) {
        assetNodes(assetKeys: $assetKeys) {
            id
            isExecutable
            configField {
                name
            }
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
                runOrError {
                    ... on Run {
                        status
                    }
                }
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

GET_AUTO_MATERIALIZE_POLICY = """
    query AssetNodeQuery {
        assetNodes {
            id
            autoMaterializePolicy {
                policyType
            }
        }
    }
"""

GET_AUTOMATION_CONDITION = """
    query AssetNodeQuery {
        assetNodes {
            id
            automationCondition {
                label
                expandedLabel
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


GET_LAST_ASSET_OBSERVATIONS = """
    query AssetGraphQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                assetObservations(limit: 1) {
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


HAS_ASSET_CHECKS = """
    query AssetNodeQuery {
        assetNodes {
            assetKey {
                path
            }
            hasAssetChecks
        }
    }
"""


GET_1D_ASSET_PARTITIONS = """
    query AssetNodeQuery($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            assetPartitionStatuses {
                ... on TimePartitionStatuses {
                    ranges {
                        startTime
                        endTime
                        startKey
                        endKey
                        status
                    }
                }
                ... on DefaultPartitionStatuses {
                    materializedPartitions
                    failedPartitions
                    unmaterializedPartitions
                    materializingPartitions
                }
            }
            partitionKeysByDimension {
                partitionKeys
            }
            partitionDefinition {
                name
            }
        }
    }
"""

GET_2D_ASSET_PARTITIONS = """
    query MaterializationStatusByDimension($pipelineSelector: PipelineSelector!) {
        assetNodes(pipeline: $pipelineSelector) {
            id
            assetPartitionStatuses {
                ... on MultiPartitionStatuses {
                    ranges {
                        primaryDimStartKey
                        primaryDimEndKey
                        primaryDimStartTime
                        primaryDimEndTime
                        secondaryDim {
                            ... on TimePartitionStatuses {
                                ranges {
                                    startTime
                                    endTime
                                    startKey
                                    endKey
                                    status
                                }
                            }
                            ... on DefaultPartitionStatuses {
                                materializedPartitions
                                failedPartitions
                                unmaterializedPartitions
                                materializingPartitions
                            }
                        }
                    }
                }
            }
            partitionDefinition {
                name
                dimensionTypes {
                    dynamicPartitionsDefinitionName
                    name
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
                numMaterializing
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

GET_ASSET_IS_OBSERVABLE = """
    query AssetQuery($assetKey: AssetKeyInput!) {
        assetOrError(assetKey: $assetKey) {
            ... on Asset {
                definition {
                    assetKey {
                        path
                    }
                    isObservable
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

GET_ASSET_OWNERS = """
    query AssetOwnersQuery($assetKeys: [AssetKeyInput!]) {
        assetNodes(assetKeys: $assetKeys) {
            assetKey {
                path
            }
            owners {
                ... on TeamAssetOwner {
                    team
                }
                ... on UserAssetOwner {
                    email
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

GET_ASSET_JOB_NAMES = """
    query($selector: RepositorySelector!) {
        repositoryOrError(repositorySelector: $selector) {
            ... on Repository {
                 assetNodes {
                      assetKey {path}
                      jobNames
                 }
            }
        }
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

GET_ASSET_BACKFILL_POLICY = """
    query AssetNodeQuery($assetKey: AssetKeyInput!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                assetKey {
                    path
                }
                backfillPolicy {
                    maxPartitionsPerRun
                    policyType
                    description
                }
            }
        }
    }
"""


GET_TAGS = """
    query AssetNodeQuery($assetKey: AssetKeyInput!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                assetKey {
                    path
                }
                tags {
                    key
                    value
                }
            }
        }
    }
"""

GET_KINDS = """
    query AssetNodeQuery($assetKey: AssetKeyInput!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                assetKey {
                    path
                }
                kinds
            }
        }
    }
"""

GET_TARGETING_INSTIGATORS = """
    query AssetNodeQuery($assetKey: AssetKeyInput!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                targetingInstigators {
                    ... on Schedule {
                        id
                        name
                    }
                    ... on Sensor {
                        id
                        name
                    }
                }
            }
        }
    }
"""

GET_ASSET_DEPENDENCIES_PARTITION_MAPPING = """
    query AssetNodeQuery($assetKey: AssetKeyInput!) {
        assetNodeOrError(assetKey: $assetKey) {
            ...on AssetNode {
                assetKey {
                    path
                }
                dependencies {
                    asset {
                        assetKey {
                            path
                        }
                    }
                    partitionMapping {
                        className
                        description
                    }
                }
            }
        }
    }
"""


def _create_run(
    graphql_context: WorkspaceRequestContext,
    pipeline_name: str,
    mode: str = "default",
    step_keys: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[GqlAssetKey]] = None,
    tags: Optional[Sequence[GqlTag]] = None,
) -> str:
    if asset_selection:
        selector = infer_job_selector(
            graphql_context, pipeline_name, asset_selection=asset_selection
        )
    else:
        selector = infer_job_selector(
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
    graphql_context: WorkspaceRequestContext,
    job_name: str,
    partition_key: str,
    asset_selection: Optional[List[AssetKey]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> str:
    base_partition_tags: Sequence[GqlTag] = [
        {"key": "dagster/partition", "value": partition_key},
        {"key": "dagster/partition_set", "value": f"{job_name}_partition_set"},
    ]
    multi_partition_tags: Sequence[GqlTag] = (
        [
            {"key": f"dagster/partition/{dimension_name}", "value": key}
            for dimension_name, key in partition_key.keys_by_dimension.items()
        ]
        if isinstance(partition_key, MultiPartitionKey)
        else []
    )
    asset_selection_tags: Sequence[GqlTag] = (
        [
            {
                "key": "dagster/step_selection",
                "value": ",".join([asset.path[-1] for asset in asset_selection]),
            }
        ]
        if asset_selection
        else []
    )
    custom_tags: Sequence[GqlTag] = [{"key": k, "value": v} for k, v in (tags or {}).items()]
    all_tags: Sequence[GqlTag] = [
        *base_partition_tags,
        *asset_selection_tags,
        *multi_partition_tags,
        *custom_tags,
    ]

    return _create_run(
        graphql_context,
        job_name,
        asset_selection=(
            [{"path": asset_key.path} for asset_key in asset_selection] if asset_selection else None
        ),
        tags=all_tags,
    )


def _get_sorted_materialization_events(
    graphql_context: WorkspaceRequestContext, run_id: str
) -> Sequence[EventLogEntry]:
    return sorted(
        [
            event
            for event in graphql_context.instance.all_logs(run_id=run_id)
            if event.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION
        ],
        key=lambda event: event.get_dagster_event().asset_key,  # type: ignore  # (possible none)
    )


class TestAssetAwareEventLog(ExecutingGraphQLContextTestMatrix):
    def test_all_asset_keys(self, graphql_context: WorkspaceRequestContext, snapshot):
        _create_run(graphql_context, "multi_asset_job")
        result = execute_dagster_graphql(graphql_context, GET_ASSETS_QUERY)
        assert result.data
        assert result.data["assetsOrError"]
        assert result.data["assetsOrError"]["nodes"]

        # sort by materialization asset key to keep list order is consistent for snapshot
        result.data["assetsOrError"]["nodes"].sort(key=lambda e: e["key"]["path"][0])

        snapshot.assert_match(result.data)

    def test_asset_key_pagination(self, graphql_context: WorkspaceRequestContext):
        _create_run(graphql_context, "multi_asset_job")

        result = execute_dagster_graphql(graphql_context, GET_ASSETS_QUERY)
        assert result.data
        assert result.data["assetsOrError"]

        nodes = result.data["assetsOrError"]["nodes"]
        assert len(nodes) > 0

        assert (
            result.data["assetsOrError"]["cursor"]
            == AssetKey(result.data["assetsOrError"]["nodes"][-1]["key"]["path"]).to_string()
        )

        all_asset_keys = [
            json.dumps(node["key"]["path"]) for node in result.data["assetsOrError"]["nodes"]
        ]

        limit = 5

        # Paginate after asset not in graph
        asset_b_index = all_asset_keys.index(AssetKey("b").to_string())

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSETS_QUERY,
            variables={"limit": 5, "cursor": AssetKey("b").to_string()},
        )

        assert (
            result.data["assetsOrError"]["nodes"]
            == nodes[asset_b_index + 1 : asset_b_index + 1 + limit]
        )

        cursor = result.data["assetsOrError"]["cursor"]
        assert (
            cursor
            == AssetKey(result.data["assetsOrError"]["nodes"][limit - 1]["key"]["path"]).to_string()
        )

        # Paginate after asset in graph

        cursor = AssetKey("asset_2").to_string()

        asset_2_index = all_asset_keys.index(cursor)
        assert asset_2_index > 0

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSETS_QUERY,
            variables={"limit": 5, "cursor": cursor},
        )

        assert (
            result.data["assetsOrError"]["nodes"]
            == nodes[asset_2_index + 1 : asset_2_index + 1 + limit]
        )

        cursor = result.data["assetsOrError"]["cursor"]
        assert (
            cursor
            == AssetKey(result.data["assetsOrError"]["nodes"][limit - 1]["key"]["path"]).to_string()
        )

    def test_get_asset_key_materialization(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        _create_run(graphql_context, "single_asset_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["a"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_asset_key_not_found(self, graphql_context: WorkspaceRequestContext, snapshot):
        _create_run(graphql_context, "single_asset_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION,
            variables={"assetKey": {"path": ["bogus", "asset"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    def test_get_partitioned_asset_key_materialization(
        self, graphql_context: WorkspaceRequestContext, snapshot
    ):
        _create_run(graphql_context, "partitioned_asset_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_WITH_PARTITION,
            variables={"assetKey": {"path": ["a"]}},
        )
        assert result.data
        snapshot.assert_match(result.data)

    @pytest.mark.parametrize(
        "event_type,asset_key,partitions,description",
        [
            (
                DagsterEventType.ASSET_MATERIALIZATION,
                AssetKey("asset1"),
                None,
                None,
            ),
            (
                DagsterEventType.ASSET_MATERIALIZATION,
                AssetKey("asset1"),
                None,
                "runless materialization",
            ),
            (
                DagsterEventType.ASSET_MATERIALIZATION,
                AssetKey("asset1"),
                ["partition1", "partition2"],
                None,
            ),
            (
                DagsterEventType.ASSET_OBSERVATION,
                AssetKey("asset1"),
                ["partition1", "partition2"],
                "runless observation",
            ),
        ],
    )
    def test_report_runless_asset_events(
        self,
        graphql_context: WorkspaceRequestContext,
        event_type: DagsterEventType,
        asset_key: AssetKey,
        partitions: Optional[Sequence[str]],
        description: Optional[str],
    ):
        assert graphql_context.instance.all_asset_keys() == []

        result = execute_dagster_graphql(
            graphql_context,
            REPORT_RUNLESS_ASSET_EVENTS,
            variables={
                "eventParams": {
                    "eventType": event_type.value,
                    "assetKey": {"path": asset_key.path},
                    "partitionKeys": partitions,
                    "description": description,
                }
            },
        )

        assert result.data
        assert result.data["reportRunlessAssetEvents"]
        assert (
            result.data["reportRunlessAssetEvents"]["__typename"]
            == "ReportRunlessAssetEventsSuccess"
        )

        # just make sure we have a limit more than the number of partitions
        limit = len(partitions) + 1 if partitions else 2
        if event_type == DagsterEventType.ASSET_MATERIALIZATION:
            event_records = graphql_context.instance.fetch_materializations(
                asset_key, ascending=True, limit=limit
            ).records
        else:
            assert event_type == DagsterEventType.ASSET_OBSERVATION
            event_records = graphql_context.instance.fetch_observations(
                asset_key, ascending=True, limit=limit
            ).records

        if partitions:
            assert len(event_records) == len(partitions)
        else:
            assert len(event_records) == 1

        for i in range(len(event_records)):
            assert event_records[i].event_log_entry.dagster_event_type == event_type
            assert event_records[i].partition_key == (partitions[i] if partitions else None)
            if event_type == DagsterEventType.ASSET_MATERIALIZATION:
                materialization = event_records[i].asset_materialization
                assert materialization
                assert materialization.description == description
            else:
                observation = event_records[i].asset_observation
                assert observation
                assert observation.description == description

    def test_asset_asof_timestamp(self, graphql_context: WorkspaceRequestContext):
        _create_run(graphql_context, "asset_tag_job")
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
        _create_run(graphql_context, "asset_tag_job")
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

    def test_asset_node_in_pipeline_that_does_not_exist(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "two_assets_job")
        selector["repositoryLocationName"] = "does_not_exist"

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_NODES_FROM_KEYS,
            variables={
                "pipelineSelector": selector,
                "assetKeys": [{"path": ["asset_one"]}],
            },
        )
        assert result.data
        assert len(result.data["assetNodes"]) == 0

    def test_asset_node_in_pipeline(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "two_assets_job")
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
        assert asset_node["hasReportRunlessAssetEventPermission"]

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

    def test_asset_node_is_executable(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_IS_EXECUTABLE,
            variables={
                "assetKeys": [
                    {"path": ["executable_asset"]},
                    {"path": ["unexecutable_asset"]},
                ],
            },
        )
        assert result.data
        assert result.data["assetNodes"]

        assert len(result.data["assetNodes"]) == 2
        exec_asset_node = result.data["assetNodes"][0]
        assert exec_asset_node["isExecutable"] is True
        unexec_asset_node = result.data["assetNodes"][1]
        assert unexec_asset_node["isExecutable"] is False

    def test_asset_partitions_in_pipeline(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "two_assets_job")
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

        selector = infer_job_selector(graphql_context, "static_partitioned_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )

        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 4
        asset_node = result.data["assetNodes"][0]
        assert asset_node["partitionKeys"] and asset_node["partitionKeys"] == [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
        ]
        asset_node = result.data["assetNodes"][1]
        assert asset_node["partitionKeys"] and asset_node["partitionKeys"] == [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
        ]

        selector = infer_job_selector(graphql_context, "time_partitioned_assets_job")
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

    def test_latest_materialization_per_partition(self, graphql_context: WorkspaceRequestContext):
        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="c")
        _create_partitioned_run(graphql_context, "partition_materialization_job", partition_key="d")
        counter = Counter()
        traced_counter.set(counter)

        selector = infer_job_selector(graphql_context, "partition_materialization_job")

        result = execute_dagster_graphql(
            graphql_context,
            GET_LATEST_MATERIALIZATION_PER_PARTITION,
            variables={"pipelineSelector": selector, "partitions": ["c", "d"]},
        )

        counts = counter.counts()
        assert counts.get("DagsterInstance.get_run_records") == 1

        assert result.data
        assert result.data["assetNodes"]
        asset_node = result.data["assetNodes"][0]
        assert len(asset_node["latestMaterializationByPartition"]) == 2
        materialization = asset_node["latestMaterializationByPartition"][0]
        run_status = materialization["runOrError"]["status"]
        assert run_status == "SUCCESS"

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
        run_status = materialization["runOrError"]["status"]
        assert run_status == "SUCCESS"

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

    def test_latest_run_for_partition(self, graphql_context: WorkspaceRequestContext):
        run_id = _create_partitioned_run(
            graphql_context, "partition_materialization_job", partition_key="a"
        )

        selector = infer_job_selector(graphql_context, "partition_materialization_job")
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

    def test_materialization_used_data(self, graphql_context: WorkspaceRequestContext):
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

    def test_default_partitions(self, graphql_context: WorkspaceRequestContext) -> None:
        # test for unpartitioned asset
        selector = infer_job_selector(graphql_context, "two_assets_job")
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
        selector = infer_job_selector(graphql_context, "partition_materialization_job")
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
        failed_partitions = result.data["assetNodes"][0]["assetPartitionStatuses"][
            "failedPartitions"
        ]
        assert len(failed_partitions) == 0
        assert (
            len(result.data["assetNodes"][0]["assetPartitionStatuses"]["unmaterializedPartitions"])
            == 4
        )
        assert (
            len(result.data["assetNodes"][0]["assetPartitionStatuses"]["materializingPartitions"])
            == 0
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

        graphql_context.clear_loaders()

        selector = infer_job_selector(graphql_context, "partition_materialization_job")
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

        graphql_context.clear_loaders()

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

    def test_partition_stats(self, graphql_context: WorkspaceRequestContext):
        _create_partitioned_run(
            graphql_context, "fail_partition_materialization_job", partition_key="b"
        )
        selector = infer_job_selector(graphql_context, "fail_partition_materialization_job")

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
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterializing"] == 0

        _create_partitioned_run(
            graphql_context,
            "fail_partition_materialization_job",
            partition_key="a",
            tags={"fail": "true"},
        )

        graphql_context.clear_loaders()

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
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterializing"] == 0

        # failing a partition that already materialized removes it from the numMaterialized count
        _create_partitioned_run(
            graphql_context,
            "fail_partition_materialization_job",
            partition_key="b",
            tags={"fail": "true"},
        )

        graphql_context.clear_loaders()

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
        assert result.data["assetNodes"][0]["partitionStats"]["numMaterializing"] == 0

        # in progress partitions that have both materialized and failed before don't screw up materialized counts

        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "executionMetadata": {"tags": [{"key": "dagster/partition", "value": "b"}]},
                }
            },
        )
        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        assert not result.errors
        assert result.data

        graphql_context.clear_loaders()

        stats_result = execute_dagster_graphql(
            graphql_context,
            GET_PARTITION_STATS,
            variables={"pipelineSelector": selector},
        )

        graphql_context.instance.run_launcher.terminate(run_id)

        assert stats_result.data
        assert stats_result.data["assetNodes"]
        assert len(stats_result.data["assetNodes"]) == 1
        assert stats_result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4
        assert stats_result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 0
        assert stats_result.data["assetNodes"][0]["partitionStats"]["numFailed"] == 1
        assert stats_result.data["assetNodes"][0]["partitionStats"]["numMaterializing"] == 1

    def test_dynamic_partitions(self, graphql_context: WorkspaceRequestContext):
        counter = Counter()
        traced_counter.set(counter)
        selector = infer_job_selector(graphql_context, "dynamic_partitioned_assets_job")

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

        counts = counter.counts()
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

    def test_time_partitions(self, graphql_context: WorkspaceRequestContext):
        def _get_datetime_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d-%H:%M")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test for hourly partitioned asset
        # First test that no partitions are materialized
        selector = infer_job_selector(graphql_context, "time_partitioned_assets_job")
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

        graphql_context.clear_loaders()

        selector = infer_job_selector(graphql_context, "time_partitioned_assets_job")
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

        graphql_context.clear_loaders()

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

        graphql_context.clear_loaders()

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

    def test_asset_observations(self, graphql_context: WorkspaceRequestContext):
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
        assert len(observations) == 2
        assert observations[0]["runOrError"]["jobName"] == "observation_job"

        asset_key_path = observations[0]["assetKey"]["path"]
        assert asset_key_path
        assert asset_key_path == ["asset_yields_observation"]

        metadata = observations[0]["metadataEntries"]
        assert metadata
        assert metadata[0]["text"] == "BAR"

        assert observations[0]["label"] == "asset_yields_observation"

        assert observations[1]["metadataEntries"][0]["text"] == "FOO"

        result = execute_dagster_graphql(
            graphql_context,
            GET_LAST_ASSET_OBSERVATIONS,
            variables={"assetKey": {"path": ["asset_yields_observation"]}},
        )

        assert result.data
        assert result.data["assetOrError"]
        observations = result.data["assetOrError"]["assetObservations"]

        assert observations
        assert len(observations) == 1
        assert observations[0]["runOrError"]["jobName"] == "observation_job"

        asset_key_path = observations[0]["assetKey"]["path"]
        assert asset_key_path
        assert asset_key_path == ["asset_yields_observation"]

        metadata = observations[0]["metadataEntries"]
        assert metadata
        assert metadata[0]["text"] == "BAR"

        assert observations[0]["label"] == "asset_yields_observation"

    def test_asset_op(self, graphql_context: WorkspaceRequestContext, snapshot):
        _create_run(graphql_context, "two_assets_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_OP,
            variables={"assetKey": {"path": ["asset_two"]}},
        )

        assert result.data
        snapshot.assert_match(result.data)

    def test_op_assets(self, graphql_context: WorkspaceRequestContext, snapshot):
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

    def test_latest_run_by_asset(self, graphql_context: WorkspaceRequestContext):
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

        graphql_context.clear_loaders()

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

        graphql_context.clear_loaders()

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

    def test_get_run_materialization(self, graphql_context: WorkspaceRequestContext, snapshot):
        _create_run(graphql_context, "single_asset_job")
        result = execute_dagster_graphql(graphql_context, GET_RUN_MATERIALIZATIONS)
        assert result.data
        assert result.data["runsOrError"]
        assert result.data["runsOrError"]["results"]
        assert len(result.data["runsOrError"]["results"]) == 1
        assert len(result.data["runsOrError"]["results"][0]["assetMaterializations"]) == 1
        snapshot.assert_match(result.data)

    def test_asset_selection_in_run(self, graphql_context: WorkspaceRequestContext):
        # Generate materializations for bar asset
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run and run.is_finished
        assert run.status == DagsterRunStatus.SUCCESS
        assert run.asset_selection == {AssetKey("bar")}

    def test_execute_job_subset(self, graphql_context: WorkspaceRequestContext):
        # Assets foo and bar are upstream dependencies of asset foo_bar

        # Execute subselection with asset bar
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run and run.is_finished
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
        assert run and run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("foo")
        assert events[1].get_dagster_event().asset_key == AssetKey("foo_bar")

    def test_execute_dependent_subset(self, graphql_context: WorkspaceRequestContext):
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
        assert run and run.is_success

        # Generate materializations with subselection of foo and baz
        run_id = _create_run(
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["baz"]}],
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run and run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("baz")
        assert events[1].get_dagster_event().asset_key == AssetKey("foo")

    def test_execute_unconnected_subset(self, graphql_context: WorkspaceRequestContext):
        # Assets "foo" and "unconnected" are disconnected assets
        run_id = _create_run(
            graphql_context,
            "foo_job",
            asset_selection=[{"path": ["foo"]}, {"path": ["unconnected"]}],
        )
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run and run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 2
        assert events[0].get_dagster_event().asset_key == AssetKey("foo")
        assert events[1].get_dagster_event().asset_key == AssetKey("unconnected")

    def test_reexecute_subset(self, graphql_context: WorkspaceRequestContext):
        run_id = _create_run(graphql_context, "foo_job", asset_selection=[{"path": ["bar"]}])
        run = graphql_context.instance.get_run_by_id(run_id)
        assert run and run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 1
        assert events[0].get_dagster_event().asset_key == AssetKey("bar")
        assert run.asset_selection == {AssetKey("bar")}

        selector = infer_job_selector(
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
        assert run and run.is_finished
        events = _get_sorted_materialization_events(graphql_context, run_id)
        assert len(events) == 1
        assert events[0].get_dagster_event().asset_key == AssetKey("bar")
        assert run.asset_selection == {AssetKey("bar")}

    def test_named_groups(self, graphql_context: WorkspaceRequestContext):
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

    def test_asset_owners(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_OWNERS,
            variables={"assetKeys": [{"path": ["asset_1"]}]},
        )

        assert result.data
        assert result.data["assetNodes"]
        assert len(result.data["assetNodes"]) == 1
        assert result.data["assetNodes"][0]["assetKey"] == {"path": ["asset_1"]}
        owners = result.data["assetNodes"][0]["owners"]
        assert len(owners) == 2
        assert owners[0]["email"] == "user@dagsterlabs.com"
        assert owners[1]["team"] == "team1"

    def test_typed_assets(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "typed_assets")
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

    def test_batch_fetch_only_once(self, graphql_context: WorkspaceRequestContext):
        counter = Counter()
        traced_counter.set(counter)
        result = execute_dagster_graphql(
            graphql_context,
            BATCH_LOAD_ASSETS,
            variables={
                "assetKeys": [{"path": ["int_asset"]}, {"path": ["str_asset"]}],
            },
        )
        assert result.data
        counts = counter.counts()
        assert len(counts) == 1
        assert counts.get("DagsterInstance.get_asset_records") == 1

    def test_batch_empty_list(self, graphql_context: WorkspaceRequestContext):
        traced_counter.set(Counter())
        result = execute_dagster_graphql(
            graphql_context,
            BATCH_LOAD_ASSETS,
            variables={
                "assetKeys": [],
            },
        )
        assert result.data
        assert len(result.data["assetNodes"]) == 0

    def test_batch_null_keys(self, graphql_context: WorkspaceRequestContext):
        traced_counter.set(Counter())
        result = execute_dagster_graphql(
            graphql_context,
            BATCH_LOAD_ASSETS,
            variables={
                "assetKeys": None,
            },
        )
        assert result.data
        assert len(result.data["assetNodes"]) > 0

    def test_get_partitions_by_dimension(self, graphql_context: WorkspaceRequestContext):
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

    def test_multipartitions_get_materialization_status(
        self, graphql_context: WorkspaceRequestContext
    ):
        selector = infer_job_selector(graphql_context, "no_multipartitions_job")
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        assert result.data
        assert result.data["assetNodes"]
        assert result.data["assetNodes"][0]["assetPartitionStatuses"]["ranges"] == []

    def test_multipartitions_get_status(self, graphql_context: WorkspaceRequestContext):
        def _get_date_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_job_selector(graphql_context, "multipartitions_job")
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

        graphql_context.clear_loaders()

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
            assert len(ranges[range_idx]["secondaryDim"]["materializingPartitions"]) == 0

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
        assert len(ranges[0]["secondaryDim"]["materializingPartitions"]) == 0
        # 2022-01-04 should have a...b materialized
        assert ranges[1]["primaryDimStartKey"] == "2022-01-04"
        assert ranges[1]["primaryDimEndKey"] == "2022-01-04"
        assert ranges[1]["primaryDimStartTime"] == _get_date_float("2022-01-04")
        assert ranges[1]["primaryDimEndTime"] == _get_date_float("2022-01-05")
        assert len(ranges[1]["secondaryDim"]["materializedPartitions"]) == 2
        assert set(ranges[1]["secondaryDim"]["materializedPartitions"]) == set(["a", "b"])
        assert len(ranges[1]["secondaryDim"]["failedPartitions"]) == 0
        assert len(ranges[1]["secondaryDim"]["materializingPartitions"]) == 0
        # multipartitions_2 should have no materialized partitions
        assert result.data["assetNodes"][1]["assetPartitionStatuses"]["ranges"] == []

    def test_multipartitions_get_failed_status(self, graphql_context: WorkspaceRequestContext):
        def _get_date_float(dt_str):
            return (
                datetime.datetime.strptime(dt_str, "%Y-%m-%d")
                .replace(tzinfo=datetime.timezone.utc)
                .timestamp()
            )

        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_job_selector(graphql_context, "multipartitions_fail_job")
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

        graphql_context.clear_loaders()

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
            assert len(ranges[range_idx]["secondaryDim"]["materializingPartitions"]) == 0
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

        graphql_context.clear_loaders()

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

        graphql_context.clear_loaders()

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

    def test_dynamic_dim_in_multipartitions_def(self, graphql_context: WorkspaceRequestContext):
        # Test that when unmaterialized, no materialized partitions are returned
        selector = infer_job_selector(graphql_context, "dynamic_in_multipartitions_success_job")
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

        graphql_context.clear_loaders()

        counter = Counter()
        traced_counter.set(counter)
        result = execute_dagster_graphql(
            graphql_context,
            GET_2D_ASSET_PARTITIONS,
            variables={"pipelineSelector": selector},
        )
        counts = counter.counts()
        assert counts.get("DagsterInstance.get_dynamic_partitions") == 1

        assert result.data
        assert result.data["assetNodes"]

        assert result.data["assetNodes"][0]["partitionDefinition"] == {
            "dimensionTypes": [
                {"dynamicPartitionsDefinitionName": "dynamic", "name": "dynamic"},
                {"dynamicPartitionsDefinitionName": None, "name": "static"},
            ],
            "name": None,
        }

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

    def test_freshness_info(self, graphql_context: WorkspaceRequestContext, snapshot):
        _create_run(graphql_context, "fresh_diamond_assets_job")
        result = execute_dagster_graphql(graphql_context, GET_FRESHNESS_INFO)

        assert result.data
        assert result.data["assetNodes"]

        snapshot.assert_match(result.data)

    def test_auto_materialize_policy(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(graphql_context, GET_AUTO_MATERIALIZE_POLICY)

        assert result.data
        assert result.data["assetNodes"]

        fresh_diamond_bottom = [
            a
            for a in result.data["assetNodes"]
            if a["id"] == 'test.test_repo.["fresh_diamond_bottom"]'
        ]
        assert len(fresh_diamond_bottom) == 1
        assert fresh_diamond_bottom[0]["autoMaterializePolicy"]["policyType"] == "LAZY"

    def test_automation_condition(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(graphql_context, GET_AUTOMATION_CONDITION)

        assert result.data
        assert result.data["assetNodes"]

        automation_condition_asset = [
            a
            for a in result.data["assetNodes"]
            if a["id"] == 'test.test_repo.["asset_with_automation_condition"]'
        ]
        assert len(automation_condition_asset) == 1
        condition = automation_condition_asset[0]["automationCondition"]
        assert condition["label"] == "eager"
        assert "(in_latest_time_window)" in condition["expandedLabel"]

        custom_automation_condition_asset = [
            a
            for a in result.data["assetNodes"]
            if a["id"] == 'test.test_repo.["asset_with_custom_automation_condition"]'
        ]
        assert len(custom_automation_condition_asset) == 1
        condition = custom_automation_condition_asset[0]["automationCondition"]
        assert condition["label"] is None
        assert condition["expandedLabel"] == ["(some_custom_name)", "SINCE", "(handled)"]

    def test_tags(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_TAGS,
            variables={
                "assetKey": {"path": ["second_kinds_key"]},
            },
        )

        second_kinds_key = result.data["assetNodeOrError"]
        assert second_kinds_key["tags"] == [{"key": "dagster/kind/python", "value": ""}]

    def test_kinds(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_KINDS,
            variables={
                "assetKey": {"path": ["first_kinds_key"]},
            },
        )

        first_kinds_key = result.data["assetNodeOrError"]
        assert set(first_kinds_key["kinds"]) == {"python", "airflow"}

        result = execute_dagster_graphql(
            graphql_context,
            GET_KINDS,
            variables={
                "assetKey": {"path": ["second_kinds_key"]},
            },
        )

        second_kinds_key = result.data["assetNodeOrError"]
        assert set(second_kinds_key["kinds"]) == {"python"}

        result = execute_dagster_graphql(
            graphql_context,
            GET_KINDS,
            variables={
                "assetKey": {"path": ["third_kinds_key"]},
            },
        )

        third_kinds_key = result.data["assetNodeOrError"]
        assert set(third_kinds_key["kinds"]) == {"python"}

        result = execute_dagster_graphql(
            graphql_context,
            GET_KINDS,
            variables={
                "assetKey": {"path": ["fourth_kinds_key"]},
            },
        )

        fourth_kinds_key = result.data["assetNodeOrError"]
        assert set(fourth_kinds_key["kinds"]) == {"python"}

    def test_has_asset_checks(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(graphql_context, HAS_ASSET_CHECKS)

        assert result.data
        assert result.data["assetNodes"]

        for a in result.data["assetNodes"]:
            if a["assetKey"]["path"] in [["asset_1"], ["one"], ["check_in_op_asset"]]:
                assert a["hasAssetChecks"] is True
            else:
                assert a["hasAssetChecks"] is False, f"Asset {a['assetKey']} has asset checks"

    def test_get_targeting_instigators(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_TARGETING_INSTIGATORS,
            variables={
                "assetKey": {"path": ["fresh_diamond_bottom"]},
            },
        )

        targeting_instigators = result.data["assetNodeOrError"]["targetingInstigators"]
        assert len(targeting_instigators) == 2
        assert set(
            targeting_instigator["name"] for targeting_instigator in targeting_instigators
        ) == {"my_auto_materialize_sensor", "every_asset_sensor"}

        result = execute_dagster_graphql(
            graphql_context,
            GET_TARGETING_INSTIGATORS,
            variables={
                "assetKey": {"path": ["upstream_dynamic_partitioned_asset"]},
            },
        )
        targeting_instigators = result.data["assetNodeOrError"]["targetingInstigators"]
        assert len(targeting_instigators) == 2

        assert set(
            targeting_instigator["name"] for targeting_instigator in targeting_instigators
        ) == {"dynamic_partition_requesting_sensor", "every_asset_sensor"}

        result = execute_dagster_graphql(
            graphql_context,
            GET_TARGETING_INSTIGATORS,
            variables={
                "assetKey": {"path": ["typed_asset"]},
            },
        )
        targeting_instigators = result.data["assetNodeOrError"]["targetingInstigators"]
        assert len(targeting_instigators) == 2

        assert set(
            targeting_instigator["name"] for targeting_instigator in targeting_instigators
        ) == {"asset_job_schedule", "every_asset_sensor"}

    def test_get_backfill_policy(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_BACKFILL_POLICY,
            variables={
                "assetKey": {"path": ["single_run_backfill_policy_asset"]},
            },
        )

        assert result.data["assetNodeOrError"]["assetKey"]["path"] == [
            "single_run_backfill_policy_asset"
        ]
        assert result.data["assetNodeOrError"]["backfillPolicy"]["policyType"] == "SINGLE_RUN"
        assert result.data["assetNodeOrError"]["backfillPolicy"]["maxPartitionsPerRun"] is None
        assert (
            result.data["assetNodeOrError"]["backfillPolicy"]["description"]
            == "Backfills all partitions in a single run"
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_BACKFILL_POLICY,
            variables={
                "assetKey": {"path": ["multi_run_backfill_policy_asset"]},
            },
        )

        assert result.data["assetNodeOrError"]["assetKey"]["path"] == [
            "multi_run_backfill_policy_asset"
        ]
        assert result.data["assetNodeOrError"]["backfillPolicy"]["policyType"] == "MULTI_RUN"
        assert result.data["assetNodeOrError"]["backfillPolicy"]["maxPartitionsPerRun"] == 10
        assert (
            result.data["assetNodeOrError"]["backfillPolicy"]["description"]
            == "Backfills in multiple runs, with a maximum of 10 partitions per run"
        )

    def test_get_partition_mapping(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_DEPENDENCIES_PARTITION_MAPPING,
            variables={
                "assetKey": {"path": ["downstream_time_partitioned_asset"]},
            },
        )

        assert result.data["assetNodeOrError"]["assetKey"]["path"] == [
            "downstream_time_partitioned_asset"
        ]
        dependencies = result.data["assetNodeOrError"]["dependencies"]
        assert len(dependencies) == 1
        assert dependencies[0]["asset"]["assetKey"]["path"] == ["upstream_time_partitioned_asset"]
        assert dependencies[0]["partitionMapping"]["className"] == "TimeWindowPartitionMapping"
        assert (
            dependencies[0]["partitionMapping"]["description"]
            == "Maps a downstream partition to any upstream partition with an overlapping time window."
        )


# This is factored out of TestAssetAwareEventLog because there is a separate implementation for plus
# graphql tests.
class TestAssetWipe(ExecutingGraphQLContextTestMatrix):
    def test_asset_wipe(self, graphql_context: WorkspaceRequestContext):
        # run to create materialization
        _create_partitioned_run(graphql_context, "integers_asset_job", "0")

        asset_keys = graphql_context.instance.all_asset_keys()
        assert AssetKey("integers_asset") in asset_keys

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_WITH_PARTITION,
            variables={"assetKey": {"path": ["integers_asset"]}},
        )

        mat = result.data["assetOrError"]["assetMaterializations"][0]
        assert mat["partition"] == "0"

        # wipe
        result = execute_dagster_graphql(
            graphql_context,
            WIPE_ASSETS,
            variables={"assetPartitionRanges": [{"assetKey": {"path": ["integers_asset"]}}]},
        )

        assert result.data
        assert result.data["wipeAssets"]
        assert result.data["wipeAssets"]["__typename"] == "AssetWipeSuccess"
        assert result.data["wipeAssets"]["assetPartitionRanges"][0]["assetKey"]["path"] == [
            "integers_asset"
        ]
        assert result.data["wipeAssets"]["assetPartitionRanges"][0]["partitionRange"] is None

        asset_keys = graphql_context.instance.all_asset_keys()
        assert AssetKey("integers_asset") not in asset_keys

        # run again to create another materialization
        _create_partitioned_run(graphql_context, "integers_asset_job", "0")

        asset_keys = graphql_context.instance.all_asset_keys()
        assert AssetKey("integers_asset") in asset_keys

        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_MATERIALIZATION_WITH_PARTITION,
            variables={"assetKey": {"path": ["integers_asset"]}},
        )

        mat = result.data["assetOrError"]["assetMaterializations"][0]
        assert mat["partition"] == "0"

        # wipe with range
        result = execute_dagster_graphql(
            graphql_context,
            WIPE_ASSETS,
            variables={
                "assetPartitionRanges": [
                    {
                        "assetKey": {"path": ["integers_asset"]},
                        "partitions": {"range": {"start": "0", "end": "0"}},
                    }
                ]
            },
        )

        assert result.data
        assert result.data["wipeAssets"]
        assert result.data["wipeAssets"]["__typename"] == "UnsupportedOperationError"
        assert "Partitioned asset wipe is not supported yet" in result.data["wipeAssets"]["message"]

        # wipe for non-existant asset
        result = execute_dagster_graphql(
            graphql_context,
            WIPE_ASSETS,
            variables={
                "assetPartitionRanges": [
                    {
                        "assetKey": {"path": ["does_not_exist"]},
                        "partitions": {"range": {"start": "0", "end": "0"}},
                    }
                ]
            },
        )

        assert result.data
        assert result.data["wipeAssets"]
        assert result.data["wipeAssets"]["__typename"] == "AssetNotFoundError"
        assert 'Asset key ["does_not_exist"] not found' in result.data["wipeAssets"]["message"]


class TestAssetEventsReadOnly(ReadonlyGraphQLContextTestMatrix):
    def test_report_runless_asset_events_permissions(
        self,
        graphql_context: WorkspaceRequestContext,
    ):
        assert graphql_context.instance.all_asset_keys() == []

        result = execute_dagster_graphql(
            graphql_context,
            REPORT_RUNLESS_ASSET_EVENTS,
            variables={
                "eventParams": {
                    "eventType": DagsterEventType.ASSET_MATERIALIZATION,
                    "assetKey": {"path": ["asset_one"]},
                }
            },
        )

        assert result.data
        assert result.data["reportRunlessAssetEvents"]
        assert result.data["reportRunlessAssetEvents"]["__typename"] == "UnauthorizedError"

        event_records = graphql_context.instance.fetch_materializations(
            AssetKey("asset_one"), limit=1
        ).records
        assert len(event_records) == 0


class TestPersistentInstanceAssetInProgress(ExecutingGraphQLContextTestMatrix):
    def test_asset_in_progress_before_materialization(
        self, graphql_context: WorkspaceRequestContext
    ):
        """While a run has started, assets that haven't been materialized yet by that run
        return that run as in-progress.
        """
        selector = infer_job_selector(graphql_context, "hanging_job")
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
            assert assets_live_info[2]["unstartedRunIds"] == []
            assert assets_live_info[2]["inProgressRunIds"] == [run_id]

    def test_asset_in_progress_already_materialized(self, graphql_context: WorkspaceRequestContext):
        """Once a run has materialized the asset, even though the run is in progress, it is not
        returned as an in-progress run for that asset.
        """
        selector = infer_job_selector(graphql_context, "output_then_hang_job")

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
                        {"path": "output_then_hang_asset"},
                    ]
                },
            )
            graphql_context.instance.run_launcher.terminate(run_id)

            assert result.data
            assert result.data["assetsLatestInfo"]

            assets_live_info = result.data["assetsLatestInfo"]

            assets_live_info = sorted(assets_live_info, key=lambda res: res["assetKey"]["path"])
            assert len(assets_live_info) == 1

            assert assets_live_info[0]["assetKey"]["path"] == ["output_then_hang_asset"]
            assert assets_live_info[0]["latestMaterialization"] is not None
            assert assets_live_info[0]["unstartedRunIds"] == []
            assert assets_live_info[0]["inProgressRunIds"] == []

    def test_asset_unstarted_after_materialization(self, graphql_context: WorkspaceRequestContext):
        """If two runs are both queued and the first one is materialized, the second one is
        still considered 'unstarted' since it was the most recently created one.
        """
        selector = pipeline_selector_from_graphql(
            infer_job_selector(graphql_context, "hanging_job")
        )

        # Create two enqueued runs
        code_location = graphql_context.get_code_location("test")
        repository = code_location.get_repository("test_repo")
        job = repository.get_full_job("hanging_job")

        queued_runs = []

        with safe_tempfile_path() as path:
            run_config = {"resources": {"hanging_asset_resource": {"config": {"file": path}}}}

            execution_params: ExecutionParams = ExecutionParams(
                selector=selector,
                run_config=run_config,
                mode="default",
                execution_metadata=create_execution_metadata(
                    {},
                ),
                step_keys=None,
            )

            for i in range(2):
                queued_runs.append(
                    create_valid_pipeline_run(graphql_context, job, execution_params, code_location)
                )

            in_progress_run_id = queued_runs[0].run_id
            unstarted_run_id = queued_runs[1].run_id

            # Launch the first run, second run is still unstarted
            graphql_context.instance.submit_run(
                in_progress_run_id,
                workspace=graphql_context,
            )

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
            graphql_context.instance.run_launcher.terminate(in_progress_run_id)

            assert result.data
            assert result.data["assetsLatestInfo"]

            assets_live_info = result.data["assetsLatestInfo"]

            assets_live_info = sorted(assets_live_info, key=lambda res: res["assetKey"]["path"])
            assert len(assets_live_info) == 3

            # Second run is shown as unstarted since it is the most recently creatd run (the
            # in progress run is not returned in inProgressRunIds since it is not the most
            # recently created run)
            assert assets_live_info[0]["assetKey"]["path"] == ["first_asset"]
            assert assets_live_info[0]["latestMaterialization"]["runId"] == in_progress_run_id
            assert assets_live_info[0]["unstartedRunIds"] == [unstarted_run_id]
            assert assets_live_info[0]["inProgressRunIds"] == []

            assert assets_live_info[1]["assetKey"]["path"] == ["hanging_asset"]
            assert assets_live_info[1]["latestMaterialization"] is None
            assert assets_live_info[1]["unstartedRunIds"] == [unstarted_run_id]
            assert assets_live_info[1]["inProgressRunIds"] == []

            assert assets_live_info[2]["assetKey"]["path"] == ["never_runs_asset"]
            assert assets_live_info[2]["latestMaterialization"] is None
            assert assets_live_info[2]["unstartedRunIds"] == [unstarted_run_id]
            assert assets_live_info[2]["inProgressRunIds"] == []

    def test_graph_asset_in_progress(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "hanging_graph_asset_job")

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
            assert assets_live_info[0]["unstartedRunIds"] == []
            assert assets_live_info[0]["inProgressRunIds"] == [run_id]

    def test_partitioned_asset_in_progress(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "hanging_partition_asset_job")

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
                        "executionMetadata": {"tags": [{"key": "dagster/partition", "value": "a"}]},
                    }
                },
            )

            assert not result.errors
            assert result.data

            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            stats_result = execute_dagster_graphql(
                graphql_context,
                GET_PARTITION_STATS,
                variables={"pipelineSelector": selector},
            )

            partitions_result = execute_dagster_graphql(
                graphql_context,
                GET_1D_ASSET_PARTITIONS,
                variables={"pipelineSelector": selector},
            )

            graphql_context.instance.run_launcher.terminate(run_id)

            assert stats_result.data
            assert stats_result.data["assetNodes"]
            assert len(stats_result.data["assetNodes"]) == 1
            assert stats_result.data["assetNodes"][0]["partitionStats"]["numPartitions"] == 4
            assert stats_result.data["assetNodes"][0]["partitionStats"]["numMaterialized"] == 0
            assert stats_result.data["assetNodes"][0]["partitionStats"]["numFailed"] == 0
            assert stats_result.data["assetNodes"][0]["partitionStats"]["numMaterializing"] == 1

            assert partitions_result.data
            assert partitions_result.data["assetNodes"]

            assert (
                len(
                    partitions_result.data["assetNodes"][0]["assetPartitionStatuses"][
                        "materializedPartitions"
                    ]
                )
                == 0
            )
            assert (
                len(
                    partitions_result.data["assetNodes"][0]["assetPartitionStatuses"][
                        "failedPartitions"
                    ]
                )
                == 0
            )
            assert (
                len(
                    partitions_result.data["assetNodes"][0]["assetPartitionStatuses"][
                        "unmaterializedPartitions"
                    ]
                )
                == 4
            )
            assert (
                len(
                    partitions_result.data["assetNodes"][0]["assetPartitionStatuses"][
                        "materializingPartitions"
                    ]
                )
                == 1
            )


class TestCrossRepoAssetDependedBy(AllRepositoryGraphQLContextTestMatrix):
    def test_cross_repo_derived_asset_dependencies(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            CROSS_REPO_ASSET_GRAPH,
        )
        asset_nodes = result.data["assetNodes"]
        derived_asset = next(
            node
            for node in asset_nodes
            if node["id"] == 'cross_asset_repos.upstream_assets_repository.["derived_asset"]'
        )
        dependent_asset_keys = [
            {"path": ["downstream_asset1"]},
            {"path": ["downstream_asset2"]},
        ]

        result_dependent_keys = sorted(
            derived_asset["dependedByKeys"], key=lambda node: node.get("path")[0]
        )
        assert result_dependent_keys == dependent_asset_keys

    def test_cross_repo_source_asset_dependencies(self, graphql_context: WorkspaceRequestContext):
        result = execute_dagster_graphql(
            graphql_context,
            CROSS_REPO_ASSET_GRAPH,
        )
        asset_nodes = result.data["assetNodes"]
        always_source_asset = next(
            node for node in asset_nodes if "always_source_asset" in node["id"]
        )
        dependent_asset_keys = [
            {"path": ["downstream_asset1"]},
            {"path": ["downstream_asset2"]},
        ]

        result_dependent_keys = sorted(
            always_source_asset["dependedByKeys"], key=lambda node: node.get("path")[0]
        )
        assert result_dependent_keys == dependent_asset_keys

    def test_cross_repo_observable_source_asset(self, graphql_context: WorkspaceRequestContext):
        """Ensure that when retrieving an asset that is observable in one repo and not in another,
        we correctly represent it as observable when retrieving information about the asset key in
        general.
        """
        result = execute_dagster_graphql(
            graphql_context,
            GET_ASSET_IS_OBSERVABLE,
            variables={"assetKey": {"path": ["sometimes_observable_source_asset"]}},
        )
        asset = result.data["assetOrError"]
        assert asset["definition"]["assetKey"]["path"] == ["sometimes_observable_source_asset"]
        assert asset["definition"]["isObservable"] is True


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
            define_asset_job("abc_asset_job", AssetSelection.assets("abc_asset")),
            daily_asset,
            define_asset_job("daily_asset_job", AssetSelection.assets("daily_asset")),
            multipartitions_asset,
            define_asset_job(
                "multipartitions_job",
                AssetSelection.assets("multipartitions_asset"),
                partitions_def=multipartitions_def,
            ),
        ]

    return partitioned_asset_repo


def test_1d_subset_backcompat():
    with instance_for_test() as instance:
        instance.can_read_asset_status_cache = lambda: False
        assert instance.can_read_asset_status_cache() is False

        with define_out_of_process_context(
            __file__, "get_partitioned_asset_repo", instance
        ) as graphql_context:
            abc_selector = infer_job_selector(graphql_context, "abc_asset_job")
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

            daily_job_selector = infer_job_selector(graphql_context, "daily_asset_job")
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
        instance.can_read_asset_status_cache = lambda: False
        assert instance.can_read_asset_status_cache() is False

        with define_out_of_process_context(
            __file__, "get_partitioned_asset_repo", instance
        ) as graphql_context:
            multipartitions_selector = infer_job_selector(graphql_context, "multipartitions_job")
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
