from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import (
    AssetHealthStatus,
    PartitionDefinitionType,
    PartitionRangeStatus,
)
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
    GetAssetDetailsAssetsOrErrorAssetConnectionNodesAssetHealth,
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
from dagster_rest_resources.__generated__.get_asset_location import (
    GetAssetLocation,
    GetAssetLocationAssetNodeOrErrorAssetNode,
    GetAssetLocationAssetNodeOrErrorAssetNodeAssetKey,
    GetAssetLocationAssetNodeOrErrorAssetNodeRepository,
    GetAssetLocationAssetNodeOrErrorAssetNodeRepositoryLocation,
    GetAssetLocationAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.get_asset_locations import (
    GetAssetLocations,
    GetAssetLocationsAssetNodes,
    GetAssetLocationsAssetNodesAssetKey,
    GetAssetLocationsAssetNodesRepository,
    GetAssetLocationsAssetNodesRepositoryLocation,
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
from dagster_rest_resources.__generated__.get_asset_partition_definition import (
    GetAssetPartitionDefinition,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNode,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeAssetKey,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodePartitionDefinition,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodePartitionDefinitionDimensionTypes,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepository,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepositoryLocation,
    GetAssetPartitionDefinitionAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.get_asset_partition_keys import (
    GetAssetPartitionKeys,
    GetAssetPartitionKeysAssetNodeOrErrorAssetNode,
    GetAssetPartitionKeysAssetNodeOrErrorAssetNodePartitionKeyConnection,
    GetAssetPartitionKeysAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.get_asset_partition_status import (
    GetAssetPartitionStatus,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNode,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNodePartitionStats,
    GetAssetPartitionStatusAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.get_asset_partition_statuses import (
    GetAssetPartitionStatuses,
    GetAssetPartitionStatusesAssetNodeOrErrorAssetNotFoundError,
)
from dagster_rest_resources.__generated__.input_types import AssetKeyInput
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
from dagster_rest_resources.schemas.exception import DagsterPlusClientError, DagsterPlusGraphqlError


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
        latestMaterializationTimestamp=1705311000.0,
        latestFailedToMaterializeTimestamp=None,
        assetHealth=GetAssetDetailsAssetsOrErrorAssetConnectionNodesAssetHealth(
            assetHealth=AssetHealthStatus.HEALTHY,
            materializationStatus=AssetHealthStatus.HEALTHY,
            assetChecksStatus=AssetHealthStatus.HEALTHY,
            freshnessStatus=AssetHealthStatus.HEALTHY,
        ),
        definition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinition(
            description=description,
            groupName=group_name,
            computeKind="python",
            kinds=kinds or [],
            freshnessPolicy=None,
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
                        latestMaterializationTimestamp=None,
                        latestFailedToMaterializeTimestamp=None,
                        assetHealth=None,
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
                        latestMaterializationTimestamp=None,
                        latestFailedToMaterializeTimestamp=None,
                        assetHealth=None,
                        definition=GetAssetDetailsAssetsOrErrorAssetConnectionNodesDefinition(
                            description=None,
                            groupName="grp",
                            computeKind=None,
                            kinds=[],
                            freshnessPolicy=None,
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

        result = DgApiAssetApi(_client=client).get_partition_status(["marts/daily", "orders"])

        client.get_asset_partition_status.assert_called_once_with(
            asset_key=AssetKeyInput(path=["marts/daily", "orders"])
        )

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
            DgApiAssetApi(_client=client).get_partition_status(["test", "asset"])

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_status.return_value = GetAssetPartitionStatus(
            assetNodeOrError=GetAssetPartitionStatusAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error getting partition status"):
            DgApiAssetApi(_client=client).get_partition_status(["test", "asset"])


def _location_node(path: list[str], repo: str = "repo", location: str = "loc"):
    return GetAssetLocationAssetNodeOrErrorAssetNode(
        __typename="AssetNode",
        assetKey=GetAssetLocationAssetNodeOrErrorAssetNodeAssetKey(path=path),
        repository=GetAssetLocationAssetNodeOrErrorAssetNodeRepository(
            name=repo,
            location=GetAssetLocationAssetNodeOrErrorAssetNodeRepositoryLocation(name=location),
        ),
    )


class TestGetAssetLocation:
    def test_returns_repository_and_code_location(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_location.return_value = GetAssetLocation(
            assetNodeOrError=_location_node(["warehouse", "orders"])
        )

        result = DgApiAssetApi(_client=client).get_asset_location(["warehouse", "orders"])

        assert result.asset_key == "warehouse/orders"
        assert result.asset_key_parts == ["warehouse", "orders"]
        assert result.repository_name == "repo"
        assert result.code_location_name == "loc"
        client.get_asset_location.assert_called_once_with(
            asset_key=AssetKeyInput(path=["warehouse", "orders"])
        )

    def test_missing_asset_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_location.return_value = GetAssetLocation(
            assetNodeOrError=GetAssetLocationAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message="no such asset"
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Asset not found: no such asset"):
            DgApiAssetApi(_client=client).get_asset_location(["nope"])


class TestListAssetLocations:
    def test_returns_a_location_per_node(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_locations.return_value = GetAssetLocations(
            assetNodes=[
                GetAssetLocationsAssetNodes(
                    assetKey=GetAssetLocationsAssetNodesAssetKey(path=["a"]),
                    repository=GetAssetLocationsAssetNodesRepository(
                        name="repo-a",
                        location=GetAssetLocationsAssetNodesRepositoryLocation(name="loc-a"),
                    ),
                ),
                GetAssetLocationsAssetNodes(
                    assetKey=GetAssetLocationsAssetNodesAssetKey(path=["b", "c"]),
                    repository=GetAssetLocationsAssetNodesRepository(
                        name="repo-b",
                        location=GetAssetLocationsAssetNodesRepositoryLocation(name="loc-b"),
                    ),
                ),
            ]
        )

        result = DgApiAssetApi(_client=client).list_asset_locations([["a"], ["b", "c"]])

        assert result.total == 2
        assert [i.asset_key for i in result.items] == ["a", "b/c"]
        assert [i.code_location_name for i in result.items] == ["loc-a", "loc-b"]

    def test_absent_assets_are_simply_missing(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_locations.return_value = GetAssetLocations(assetNodes=[])

        result = DgApiAssetApi(_client=client).list_asset_locations([["gone"]])

        assert result.items == []


class TestListPartitionKeys:
    def test_returns_a_page_of_keys(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_keys.return_value = GetAssetPartitionKeys(
            assetNodeOrError=GetAssetPartitionKeysAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                partitionKeyConnection=GetAssetPartitionKeysAssetNodeOrErrorAssetNodePartitionKeyConnection(
                    results=["2024-01-01", "2024-01-02"], cursor="c1", hasMore=True
                ),
            )
        )

        result = DgApiAssetApi(client).list_partition_keys(
            ["marts/daily", "orders"], limit=2, cursor="c0", ascending=False
        )

        client.get_asset_partition_keys.assert_called_once_with(
            asset_key=AssetKeyInput(path=["marts/daily", "orders"]),
            limit=2,
            ascending=False,
            cursor="c0",
        )
        assert result.items == ["2024-01-01", "2024-01-02"]
        assert result.cursor == "c1"
        assert result.has_more

    def test_unpartitioned_asset_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_keys.return_value = GetAssetPartitionKeys(
            assetNodeOrError=GetAssetPartitionKeysAssetNodeOrErrorAssetNode(
                __typename="AssetNode", partitionKeyConnection=None
            )
        )
        with pytest.raises(DagsterPlusClientError, match="does not have partitions"):
            DgApiAssetApi(client).list_partition_keys(["orders"], limit=10)

    def test_asset_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_keys.return_value = GetAssetPartitionKeys(
            assetNodeOrError=GetAssetPartitionKeysAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError, match="Asset not found"):
            DgApiAssetApi(client).list_partition_keys(["missing"], limit=10)


class TestGetPartitionDefinition:
    def test_returns_dimensions_and_location(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_definition.return_value = GetAssetPartitionDefinition(
            assetNodeOrError=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetKey=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeAssetKey(
                    path=["orders"]
                ),
                repository=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepository(
                    name="repo",
                    location=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepositoryLocation(
                        name="loc"
                    ),
                ),
                partitionDefinition=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodePartitionDefinition(
                    type=PartitionDefinitionType.DYNAMIC,
                    dimensionTypes=[
                        GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodePartitionDefinitionDimensionTypes(
                            name="default",
                            type=PartitionDefinitionType.DYNAMIC,
                            dynamicPartitionsDefinitionName="customers",
                        )
                    ],
                ),
            )
        )

        result = DgApiAssetApi(client).get_partition_definition(["orders"])

        assert (result.code_location_name, result.repository_name) == ("loc", "repo")
        assert result.type == PartitionDefinitionType.DYNAMIC
        assert result.dimensions[0].dynamic_partitions_definition_name == "customers"

    def test_unpartitioned_asset_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_definition.return_value = GetAssetPartitionDefinition(
            assetNodeOrError=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetKey=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeAssetKey(
                    path=["orders"]
                ),
                repository=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepository(
                    name="repo",
                    location=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNodeRepositoryLocation(
                        name="loc"
                    ),
                ),
                partitionDefinition=None,
            )
        )
        with pytest.raises(DagsterPlusClientError, match="does not have partitions"):
            DgApiAssetApi(client).get_partition_definition(["orders"])

    def test_asset_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_definition.return_value = GetAssetPartitionDefinition(
            assetNodeOrError=GetAssetPartitionDefinitionAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError, match="Asset not found"):
            DgApiAssetApi(client).get_partition_definition(["missing"])


def _partition_statuses_response(statuses: dict, is_partitioned: bool = True):
    return GetAssetPartitionStatuses.model_validate(
        {
            "assetNodeOrError": {
                "__typename": "AssetNode",
                "assetKey": {"path": ["orders"]},
                "isPartitioned": is_partitioned,
                "assetPartitionStatuses": statuses,
            }
        }
    )


_DEFAULT_STATUSES = {
    "__typename": "DefaultPartitionStatuses",
    "materializedPartitions": ["a"],
    "failedPartitions": ["c"],
    "materializingPartitions": ["b"],
    "unmaterializedPartitions": ["d"],
}


class TestGetPartitionStatuses:
    def test_lists_keys_by_status(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            _DEFAULT_STATUSES
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"])

        client.get_asset_partition_statuses.assert_called_once_with(
            asset_key=AssetKeyInput(path=["orders"])
        )
        assert result.statuses is not None and result.statuses.keys is not None
        assert result.statuses.keys.failed == ["c"]
        assert result.statuses.keys.unmaterialized == ["d"]
        assert result.multi_ranges is None

    def test_reports_time_partitions_as_ranges(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            {
                "__typename": "TimePartitionStatuses",
                "ranges": [
                    {"startKey": "2024-01-01", "endKey": "2024-01-05", "status": "MATERIALIZED"}
                ],
            }
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"])

        assert result.statuses is not None and result.statuses.ranges is not None
        [time_range] = result.statuses.ranges
        assert (time_range.start_key, time_range.end_key) == ("2024-01-01", "2024-01-05")
        assert time_range.status == PartitionRangeStatus.MATERIALIZED

    def test_reports_multi_partitions_by_primary_range(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            {
                "__typename": "MultiPartitionStatuses",
                "primaryDimensionName": "date",
                "ranges": [
                    {
                        "primaryDimStartKey": "2024-01-01",
                        "primaryDimEndKey": "2024-01-02",
                        "secondaryDim": _DEFAULT_STATUSES,
                    },
                    {
                        "primaryDimStartKey": "2024-01-03",
                        "primaryDimEndKey": "2024-01-03",
                        "secondaryDim": {
                            "__typename": "TimePartitionStatuses",
                            "ranges": [
                                {"startKey": "00:00", "endKey": "12:00", "status": "FAILED"}
                            ],
                        },
                    },
                ],
            }
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"])

        assert result.statuses is None
        assert result.primary_dimension_name == "date"
        assert result.multi_ranges is not None
        first_range, second_range = result.multi_ranges
        assert first_range.primary_start_key == "2024-01-01"
        assert first_range.secondary.keys is not None
        assert first_range.secondary.keys.materialized == ["a"]
        assert second_range.primary_start_key == "2024-01-03"
        assert second_range.secondary.keys is None
        assert second_range.secondary.ranges is not None
        [secondary_range] = second_range.secondary.ranges
        assert (secondary_range.start_key, secondary_range.end_key) == ("00:00", "12:00")
        assert secondary_range.status == PartitionRangeStatus.FAILED

    def test_filters_keys_to_one_status(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            _DEFAULT_STATUSES
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"], status="FAILED")

        assert result.statuses is not None and result.statuses.keys is not None
        assert result.statuses.keys.failed == ["c"]
        assert result.statuses.keys.materialized is None
        assert result.statuses.keys.materializing is None
        assert result.statuses.keys.unmaterialized is None

    def test_filters_time_ranges_to_one_status(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            {
                "__typename": "TimePartitionStatuses",
                "ranges": [
                    {"startKey": "2024-01-01", "endKey": "2024-01-05", "status": "MATERIALIZED"},
                    {"startKey": "2024-01-06", "endKey": "2024-01-06", "status": "FAILED"},
                ],
            }
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"], status="FAILED")

        assert result.statuses is not None and result.statuses.ranges is not None
        [failed_range] = result.statuses.ranges
        assert (failed_range.start_key, failed_range.end_key) == ("2024-01-06", "2024-01-06")

    def test_time_partitions_cannot_be_filtered_to_unmaterialized(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            {"__typename": "TimePartitionStatuses", "ranges": []}
        )
        with pytest.raises(DagsterPlusClientError, match="cannot be filtered to UNMATERIALIZED"):
            DgApiAssetApi(client).get_partition_statuses(["orders"], status="UNMATERIALIZED")

    def test_filtering_multi_partitions_drops_ranges_without_the_status(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            {
                "__typename": "MultiPartitionStatuses",
                "primaryDimensionName": "date",
                "ranges": [
                    {
                        "primaryDimStartKey": "2024-01-01",
                        "primaryDimEndKey": "2024-01-02",
                        "secondaryDim": _DEFAULT_STATUSES,
                    },
                    {
                        "primaryDimStartKey": "2024-01-03",
                        "primaryDimEndKey": "2024-01-03",
                        "secondaryDim": {**_DEFAULT_STATUSES, "failedPartitions": []},
                    },
                ],
            }
        )

        result = DgApiAssetApi(client).get_partition_statuses(["orders"], status="FAILED")

        assert result.multi_ranges is not None
        [failed_range] = result.multi_ranges
        assert failed_range.primary_start_key == "2024-01-01"
        assert failed_range.secondary.keys is not None
        assert failed_range.secondary.keys.failed == ["c"]
        assert failed_range.secondary.keys.materialized is None

    def test_unpartitioned_asset_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = _partition_statuses_response(
            _DEFAULT_STATUSES, is_partitioned=False
        )
        with pytest.raises(DagsterPlusClientError, match="does not have partitions"):
            DgApiAssetApi(client).get_partition_statuses(["orders"])

    def test_asset_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_partition_statuses.return_value = GetAssetPartitionStatuses(
            assetNodeOrError=GetAssetPartitionStatusesAssetNodeOrErrorAssetNotFoundError(
                __typename="AssetNotFoundError", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError, match="Asset not found"):
            DgApiAssetApi(client).get_partition_statuses(["missing"])
