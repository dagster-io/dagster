from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import AssetHealthStatus
from dagster_rest_resources.__generated__.get_asset_condition_evaluations import (
    GetAssetConditionEvaluations,
    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecords,
    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecords,
    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecordsEvaluationNodes,
    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAutoMaterializeAssetEvaluationNeedsMigrationError,
)
from dagster_rest_resources.__generated__.get_asset_details import (
    GetAssetDetails,
    GetAssetDetailsAssetsOrErrorAssetConnection,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodes,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinition,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionAutomationCondition,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionBackfillPolicy,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependedByKeys,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependencies,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesAsset,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesAssetAssetKey,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesPartitionMapping,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependencyKeys,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionMetadataEntriesFloatMetadataEntry,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionMetadataEntriesTextMetadataEntry,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionOwnersTeamAssetOwner,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionOwnersUserAssetOwner,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionPartitionDefinition,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionTags,
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesKey,
    GetAssetDetailsAssetsOrErrorPythonError,
)
from dagster_rest_resources.__generated__.get_asset_health import (
    GetAssetHealth,
    GetAssetHealthAssetsOrErrorAssetConnection,
    GetAssetHealthAssetsOrErrorAssetConnectionNodes,
    GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetHealth,
    GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetHealthAssetChecksStatusMetadataAssetHealthCheckDegradedMeta,
    GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetMaterializations,
    GetAssetHealthAssetsOrErrorAssetConnectionNodesKey,
    GetAssetHealthAssetsOrErrorPythonError,
)
from dagster_rest_resources.__generated__.get_asset_materialization_events import (
    GetAssetMaterializationEvents,
    GetAssetMaterializationEventsAssetsOrErrorAssetConnection,
    GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodes,
    GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesAssetMaterializations,
    GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesAssetMaterializationsTags,
    GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesKey,
    GetAssetMaterializationEventsAssetsOrErrorPythonError,
)
from dagster_rest_resources.__generated__.get_asset_observation_events import (
    GetAssetObservationEvents,
    GetAssetObservationEventsAssetsOrErrorAssetConnection,
    GetAssetObservationEventsAssetsOrErrorAssetConnectionNodes,
    GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesAssetObservations,
    GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesAssetObservationsTags,
    GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesKey,
    GetAssetObservationEventsAssetsOrErrorPythonError,
)
from dagster_rest_resources.__generated__.get_asset_partition_status import (
    GetAssetPartitionStatus,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNode,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNodePartitionStats,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.list_asset_records import (
    ListAssetRecords,
    ListAssetRecordsAssetRecordsOrErrorAssetRecordConnection,
    ListAssetRecordsAssetRecordsOrErrorAssetRecordConnectionAssets,
    ListAssetRecordsAssetRecordsOrErrorAssetRecordConnectionAssetsKey,
    ListAssetRecordsAssetRecordsOrErrorPythonError,
)
from dagster_rest_resources.api.asset import DgApiAssetApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.asset import (
    DgApiAssetList,
    DgApiEvaluationRecordList,
    DgApiPartitionStats,
)
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError


def _make_asset_record(id: str = "asset-id", path: list[str] | None = None):
    return ListAssetRecordsAssetRecordsOrErrorAssetRecordConnectionAssets(
        id=id,
        key=ListAssetRecordsAssetRecordsOrErrorAssetRecordConnectionAssetsKey(
            path=path or ["test", "asset"]
        ),
    )


def _make_asset_detail_node(
    id: str = "asset-id",
    path: list[str] | None = None,
    group_name: str = "default",
    description: str | None = None,
    kinds: list[str] | None = None,
) -> GetAssetDetailsAssetsOrErrorAssetConnectionNodes:
    return GetAssetDetailsAssetsOrErrorAssetConnectionNodes(
        id=id,
        key=GetAssetDetailsAssetsOrErrorAssetConnectionNodesKey(path=path or ["test", "asset"]),
        definition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinition(
            description=description,
            groupName=group_name,
            kinds=kinds or [],
            dependencyKeys=[],
            metadataEntries=[],
            automationCondition=None,
            partitionDefinition=None,
            dependencies=[],
            dependedByKeys=[],
            owners=[],
            tags=[],
            backfillPolicy=None,
            jobNames=[],
        ),
    )


class TestListAssets:
    def test_returns_assets(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_records.return_value = ListAssetRecords(
            assetRecordsOrError=ListAssetRecordsAssetRecordsOrErrorAssetRecordConnection(
                __typename="AssetRecordConnection",
                assets=[_make_asset_record(id="a1", path=["test", "asset"])],
                cursor=None,
            )
        )
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorAssetConnection(
                __typename="AssetConnection",
                nodes=[_make_asset_detail_node(id="a1", path=["test", "asset"])],
            )
        )

        result = DgApiAssetApi(_client=client).list_assets(limit=10)

        assert len(result.items) == 1
        assert result.items[0].asset_key == "test/asset"
        assert result.cursor is None
        assert result.has_more is False

    def test_returns_empty_when_no_records(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_records.return_value = ListAssetRecords(
            assetRecordsOrError=ListAssetRecordsAssetRecordsOrErrorAssetRecordConnection(
                __typename="AssetRecordConnection",
                assets=[],
                cursor=None,
            )
        )

        result = DgApiAssetApi(_client=client).list_assets()

        assert result == DgApiAssetList(items=[], cursor=None, has_more=False)
        client.get_asset_details.assert_not_called()

    def test_skips_nodes_without_definition(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_records.return_value = ListAssetRecords(
            assetRecordsOrError=ListAssetRecordsAssetRecordsOrErrorAssetRecordConnection(
                __typename="AssetRecordConnection",
                assets=[_make_asset_record(id="no-def", path=["no", "def"])],
                cursor=None,
            )
        )
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorAssetConnection(
                __typename="AssetConnection",
                nodes=[
                    GetAssetDetailsAssetsOrErrorAssetConnectionNodes(
                        id="no-def",
                        key=GetAssetDetailsAssetsOrErrorAssetConnectionNodesKey(path=["no", "def"]),
                        definition=None,
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).list_assets()

        assert result.items == []

    def test_records_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_records.return_value = ListAssetRecords(
            assetRecordsOrError=ListAssetRecordsAssetRecordsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing assets"):
            DgApiAssetApi(_client=client).list_assets()

    def test_details_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_records.return_value = ListAssetRecords(
            assetRecordsOrError=ListAssetRecordsAssetRecordsOrErrorAssetRecordConnection(
                __typename="AssetRecordConnection",
                assets=[_make_asset_record()],
                cursor=None,
            )
        )
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching asset details"):
            DgApiAssetApi(_client=client).list_assets()


class TestGetAsset:
    def test_returns_asset(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorAssetConnection(
                __typename="AssetConnection",
                nodes=[
                    _make_asset_detail_node(
                        id="a1",
                        path=["test", "path"],
                        group_name="test_group",
                        description="test_desc",
                        kinds=["test_kind"],
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).get_asset("test/path")

        assert result.asset_key == "test/path"
        assert result.group_name == "test_group"
        assert result.description == "test_desc"
        assert result.kinds == ["test_kind"]

    def test_asset_with_metadata_and_owners(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorAssetConnection(
                __typename="AssetConnection",
                nodes=[
                    GetAssetDetailsAssetsOrErrorAssetConnectionNodes(
                        id="a1",
                        key=GetAssetDetailsAssetsOrErrorAssetConnectionNodesKey(path=["test/path"]),
                        definition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinition(
                            description=None,
                            groupName="grp",
                            kinds=[],
                            dependencyKeys=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependencyKeys(
                                    path=["dep"]
                                )
                            ],
                            metadataEntries=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionMetadataEntriesTextMetadataEntry(
                                    __typename="TextMetadataEntry",
                                    label="note",
                                    description=None,
                                    text="hello",
                                ),
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionMetadataEntriesFloatMetadataEntry(
                                    __typename="FloatMetadataEntry",
                                    label="score",
                                    description=None,
                                    floatValue=3.14,
                                ),
                            ],
                            automationCondition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionAutomationCondition(
                                label="eager",
                                expandedLabel=["Any", "deps", "updated"],
                            ),
                            partitionDefinition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionPartitionDefinition(
                                description="Daily [%Y-%m-%d]"
                            ),
                            dependencies=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependencies(
                                    asset=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesAsset(
                                        assetKey=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesAssetAssetKey(
                                            path=["upstream"]
                                        )
                                    ),
                                    partitionMapping=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependenciesPartitionMapping(
                                        className="TimeWindowPartitionMapping",
                                        description="same window",
                                    ),
                                )
                            ],
                            dependedByKeys=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionDependedByKeys(
                                    path=["downstream"]
                                )
                            ],
                            owners=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionOwnersUserAssetOwner(
                                    __typename="UserAssetOwner", email="user@example.com"
                                ),
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionOwnersTeamAssetOwner(
                                    __typename="TeamAssetOwner", team="data-platform"
                                ),
                            ],
                            tags=[
                                GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionTags(
                                    key="domain", value="analytics"
                                )
                            ],
                            backfillPolicy=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinitionBackfillPolicy(
                                maxPartitionsPerRun=5
                            ),
                            jobNames=["daily_job"],
                        ),
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).get_asset("test/path")

        assert result.dependency_keys == ["dep"]
        assert result.metadata_entries == [
            {"label": "note", "description": "", "text": "hello"},
            {"label": "score", "description": "", "floatValue": 3.14},
        ]
        assert result.automation_condition is not None
        assert result.automation_condition.label == "eager"
        assert result.partition_definition is not None
        assert result.upstream_dependencies is not None
        assert len(result.upstream_dependencies) == 1
        assert result.upstream_dependencies[0].asset_key == "upstream"
        assert result.upstream_dependencies[0].partition_mapping is not None
        assert result.downstream_keys == ["downstream"]
        assert result.owners == [{"email": "user@example.com"}, {"team": "data-platform"}]
        assert result.tags == [{"key": "domain", "value": "analytics"}]
        assert result.backfill_policy is not None
        assert result.backfill_policy.max_partitions_per_run == 5
        assert result.job_names == ["daily_job"]

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorAssetConnection(
                __typename="AssetConnection", nodes=[]
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Asset not found"):
            DgApiAssetApi(_client=client).get_asset("missing/path")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_details.return_value = GetAssetDetails(
            assetsOrError=GetAssetDetailsAssetsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching asset"):
            DgApiAssetApi(_client=client).get_asset("test/path")


class TestGetHealth:
    def test_returns_health(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_health.return_value = GetAssetHealth(
            assetsOrError=GetAssetHealthAssetsOrErrorAssetConnection(
                __typename="AssetConnection",
                nodes=[
                    GetAssetHealthAssetsOrErrorAssetConnectionNodes(
                        key=GetAssetHealthAssetsOrErrorAssetConnectionNodesKey(
                            path=["test", "asset"]
                        ),
                        definition=None,
                        assetHealth=GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetHealth(
                            assetHealth=AssetHealthStatus.HEALTHY,
                            materializationStatus=AssetHealthStatus.HEALTHY,
                            materializationStatusMetadata=None,
                            assetChecksStatus=AssetHealthStatus.HEALTHY,
                            assetChecksStatusMetadata=GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetHealthAssetChecksStatusMetadataAssetHealthCheckDegradedMeta(
                                __typename="AssetHealthCheckDegradedMeta",
                                numFailedChecks=1,
                                numWarningChecks=0,
                                totalNumChecks=3,
                            ),
                            freshnessStatus=AssetHealthStatus.NOT_APPLICABLE,
                            freshnessStatusMetadata=None,
                        ),
                        assetMaterializations=[
                            GetAssetHealthAssetsOrErrorAssetConnectionNodesAssetMaterializations(
                                timestamp="1706745600000",
                                runId="run-1",
                                partition=None,
                            )
                        ],
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).get_health("test/asset")

        assert result.asset_key == "test/asset"
        assert result.asset_health == "HEALTHY"
        assert result.materialization_status == "HEALTHY"
        assert result.freshness_status == "NOT_APPLICABLE"
        assert result.latest_materialization is not None
        assert result.latest_materialization.run_id == "run-1"
        assert result.checks_status is not None
        assert result.checks_status.num_failed_checks == 1
        assert result.checks_status.total_num_checks == 3

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_health.return_value = GetAssetHealth(
            assetsOrError=GetAssetHealthAssetsOrErrorAssetConnection(
                __typename="AssetConnection", nodes=[]
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Asset not found"):
            DgApiAssetApi(_client=client).get_health("missing/path")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_health.return_value = GetAssetHealth(
            assetsOrError=GetAssetHealthAssetsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching asset health"):
            DgApiAssetApi(_client=client).get_health("test/path")


class TestGetEvents:
    def _make_mat_result(self, events=None):
        nodes = []
        if events is not None:
            nodes = [
                GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodes(
                    key=GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesKey(
                        path=["test", "asset"]
                    ),
                    assetMaterializations=events,
                )
            ]
        return GetAssetMaterializationEvents(
            assetsOrError=GetAssetMaterializationEventsAssetsOrErrorAssetConnection(
                __typename="AssetConnection", nodes=nodes
            )
        )

    def _make_obs_result(self, events=None):
        nodes = []
        if events is not None:
            nodes = [
                GetAssetObservationEventsAssetsOrErrorAssetConnectionNodes(
                    key=GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesKey(
                        path=["test", "asset"]
                    ),
                    assetObservations=events,
                )
            ]
        return GetAssetObservationEvents(
            assetsOrError=GetAssetObservationEventsAssetsOrErrorAssetConnection(
                __typename="AssetConnection", nodes=nodes
            )
        )

    def test_materializations_only(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_materialization_events.return_value = self._make_mat_result(
            [
                GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesAssetMaterializations(
                    timestamp="1000",
                    runId="run-1",
                    partition=None,
                    tags=[
                        GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesAssetMaterializationsTags(
                            key="env", value="prod"
                        )
                    ],
                    metadataEntries=[],
                )
            ]
        )

        result = DgApiAssetApi(_client=client).get_events(
            "test/asset", event_type="ASSET_MATERIALIZATION"
        )

        client.get_asset_observation_events.assert_not_called()
        assert len(result.items) == 1
        assert result.items[0].event_type == "ASSET_MATERIALIZATION"
        assert result.items[0].run_id == "run-1"
        assert result.items[0].tags == [{"key": "env", "value": "prod"}]

    def test_observations_only(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_observation_events.return_value = self._make_obs_result(
            [
                GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesAssetObservations(
                    timestamp="2000",
                    runId="run-2",
                    partition=None,
                    tags=[
                        GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesAssetObservationsTags(
                            key="env", value="prod"
                        )
                    ],
                    metadataEntries=[],
                )
            ]
        )

        result = DgApiAssetApi(_client=client).get_events(
            "test/asset", event_type="ASSET_OBSERVATION"
        )

        client.get_asset_materialization_events.assert_not_called()
        assert len(result.items) == 1
        assert result.items[0].event_type == "ASSET_OBSERVATION"
        assert result.items[0].run_id == "run-2"
        assert result.items[0].tags == [{"key": "env", "value": "prod"}]

    def test_both_event_types_merged_and_sorted(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_materialization_events.return_value = self._make_mat_result(
            [
                GetAssetMaterializationEventsAssetsOrErrorAssetConnectionNodesAssetMaterializations(
                    timestamp="1000",
                    runId="run-mat",
                    partition=None,
                    tags=[],
                    metadataEntries=[],
                )
            ]
        )
        client.get_asset_observation_events.return_value = self._make_obs_result(
            [
                GetAssetObservationEventsAssetsOrErrorAssetConnectionNodesAssetObservations(
                    timestamp="2000",
                    runId="run-obs",
                    partition=None,
                    tags=[],
                    metadataEntries=[],
                )
            ]
        )

        result = DgApiAssetApi(_client=client).get_events("test/asset")

        assert len(result.items) == 2
        assert result.items[0].run_id == "run-obs"
        assert result.items[1].run_id == "run-mat"

    def test_materialization_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_materialization_events.return_value = GetAssetMaterializationEvents(
            assetsOrError=GetAssetMaterializationEventsAssetsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching asset events"):
            DgApiAssetApi(_client=client).get_events("test/asset")

    def test_observation_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_materialization_events.return_value = self._make_mat_result([])
        client.get_asset_observation_events.return_value = GetAssetObservationEvents(
            assetsOrError=GetAssetObservationEventsAssetsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching asset events"):
            DgApiAssetApi(_client=client).get_events("test/asset")


class TestGetEvaluations:
    def test_returns_evaluations(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_condition_evaluations.return_value = GetAssetConditionEvaluations(
            assetConditionEvaluationRecordsOrError=GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecords(
                __typename="AssetConditionEvaluationRecords",
                records=[
                    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecords(
                        evaluationId="1",
                        timestamp=1706745600.0,
                        numRequested=3,
                        runIds=["run-1", "run-2"],
                        startTimestamp=1706745600.0,
                        endTimestamp=1706745610.0,
                        rootUniqueId="root_1",
                        evaluationNodes=[
                            GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecordsEvaluationNodes(
                                uniqueId="root",
                                userLabel="eager",
                                expandedLabel=["Any", "deps", "updated"],
                                startTimestamp=None,
                                endTimestamp=None,
                                numTrue=5,
                                numCandidates=10,
                                isPartitioned=True,
                                childUniqueIds=[],
                                operatorType="AND",
                            )
                        ],
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).get_evaluations(
            "test/asset", limit=10, include_nodes=False
        )

        assert len(result.items) == 1
        assert result.items[0].evaluation_id == 1
        assert result.items[0].num_requested == 3
        assert result.items[0].run_ids == ["run-1", "run-2"]
        assert result.items[0].evaluation_nodes is None

    def test_returns_evaluations_with_nodes(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_condition_evaluations.return_value = GetAssetConditionEvaluations(
            assetConditionEvaluationRecordsOrError=GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecords(
                __typename="AssetConditionEvaluationRecords",
                records=[
                    GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecords(
                        evaluationId="1",
                        timestamp=1706745600.0,
                        numRequested=1,
                        runIds=[],
                        startTimestamp=None,
                        endTimestamp=None,
                        rootUniqueId="test_unique_id",
                        evaluationNodes=[
                            GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecordsRecordsEvaluationNodes(
                                uniqueId="test_unique_id",
                                userLabel="eager",
                                expandedLabel=["Any", "deps", "updated"],
                                startTimestamp=None,
                                endTimestamp=None,
                                numTrue=5,
                                numCandidates=10,
                                isPartitioned=True,
                                childUniqueIds=[],
                                operatorType="AND",
                            )
                        ],
                    )
                ],
            )
        )

        result = DgApiAssetApi(_client=client).get_evaluations(
            "test/asset", limit=10, include_nodes=True
        )

        assert result.items[0].evaluation_nodes is not None
        assert len(result.items[0].evaluation_nodes) == 1
        assert result.items[0].evaluation_nodes[0].unique_id == "test_unique_id"

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_condition_evaluations.return_value = GetAssetConditionEvaluations(
            assetConditionEvaluationRecordsOrError=GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAssetConditionEvaluationRecords(
                __typename="AssetConditionEvaluationRecords",
                records=[],
            )
        )

        result = DgApiAssetApi(_client=client).get_evaluations("test/asset")

        assert result == DgApiEvaluationRecordList(items=[])

    def test_migration_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_condition_evaluations.return_value = GetAssetConditionEvaluations(
            assetConditionEvaluationRecordsOrError=GetAssetConditionEvaluationsAssetConditionEvaluationRecordsOrErrorAutoMaterializeAssetEvaluationNeedsMigrationError(
                __typename="AutoMaterializeAssetEvaluationNeedsMigrationError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Migration required"):
            DgApiAssetApi(_client=client).get_evaluations("test/asset")


class TestGetPartitionStatus:
    def test_returns_stats(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_status.return_value = GetAssetPartitionStatus(
            assetNodeOrError=GetAssetPartitionStatusAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                partitionStats=GetAssetPartitionStatusAssetNodeOrErrorAssetNodePartitionStats(
                    numMaterialized=1,
                    numPartitions=2,
                    numFailed=3,
                    numMaterializing=4,
                ),
            )
        )

        result = DgApiAssetApi(_client=client).get_partition_status("test/asset")

        assert result == DgApiPartitionStats(
            num_materialized=1,
            num_partitions=2,
            num_failed=3,
            num_materializing=4,
        )

    def test_no_partitions_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_status.return_value = GetAssetPartitionStatus(
            assetNodeOrError=GetAssetPartitionStatusAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                partitionStats=None,
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Asset does not have partitions"):
            DgApiAssetApi(_client=client).get_partition_status("test/asset")

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_status.return_value = GetAssetPartitionStatus(
            assetNodeOrError=GetAssetPartitionStatusAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error getting partition status"):
            DgApiAssetApi(_client=client).get_partition_status("test/asset")
