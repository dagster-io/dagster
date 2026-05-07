import datetime
import logging
from dataclasses import dataclass
from typing import Any, Literal

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.get_asset_details import (
    GetAssetDetailsAssetsOrErrorAssetConnectionNodes,
)
from dagster_rest_resources.__generated__.get_asset_health import (
    GetAssetHealthAssetsOrErrorAssetConnectionNodes,
)
from dagster_rest_resources.__generated__.input_types import AssetKeyInput
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.asset import (
    DgApiAsset,
    DgApiAssetChecksStatus,
    DgApiAssetDependency,
    DgApiAssetEvent,
    DgApiAssetEventList,
    DgApiAssetFreshnessInfo,
    DgApiAssetList,
    DgApiAssetMaterialization,
    DgApiAssetStatus,
    DgApiAutomationCondition,
    DgApiBackfillPolicy,
    DgApiEvaluationNode,
    DgApiEvaluationRecord,
    DgApiEvaluationRecordList,
    DgApiPartitionDefinition,
    DgApiPartitionMapping,
    DgApiPartitionStats,
)
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DgApiAssetApi:
    _client: IGraphQLClient

    def list_assets(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> DgApiAssetList:
        """List assets with cursor-based pagination."""
        assets: list[DgApiAsset] = []
        next_cursor = cursor

        while True:
            remaining = limit - len(assets)
            record_result = self._client.list_asset_records(
                cursor=next_cursor,
                limit=remaining,
            ).asset_records_or_error

            match record_result.typename__:
                case "AssetRecordConnection":
                    records = record_result.assets  # ty: ignore[unresolved-attribute]
                    if not records:
                        next_cursor = None
                        break
                    next_cursor = record_result.cursor  # ty: ignore[unresolved-attribute]

                case "PythonError":
                    raise DagsterPlusGraphqlError(f"Error listing assets: {record_result.message}")  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)

            detail_result = self._client.get_asset_details(
                asset_keys=[AssetKeyInput(path=r.key.path) for r in records],
            ).assets_or_error

            match detail_result.typename__:
                case "AssetConnection":
                    nodes_by_key = {"/".join(n.key.path): n for n in detail_result.nodes}  # ty: ignore[unresolved-attribute]
                case "PythonError":
                    raise DagsterPlusGraphqlError(
                        f"Error fetching asset details: {detail_result.message}"  # ty: ignore[unresolved-attribute]
                    )
                case _ as unreachable:
                    assert_never(unreachable)

            for r in records:
                key = "/".join(r.key.path)
                node = nodes_by_key.get(key)
                if not node:
                    continue
                asset = self._build_asset_from_node(node)
                if asset is not None:
                    assets.append(asset)

            if len(assets) >= limit:
                assets = assets[:limit]
                break

            if next_cursor is None:
                break

        return DgApiAssetList(
            items=assets,
            cursor=next_cursor,
            has_more=next_cursor is not None,
        )

    def get_asset(self, asset_key: str) -> DgApiAsset:
        """Get single asset by slash-separated key (e.g., 'foo/bar')."""
        result = self._client.get_asset_details(
            asset_keys=[AssetKeyInput(path=asset_key.split("/"))],
        ).assets_or_error

        match result.typename__:
            case "AssetConnection":
                nodes = result.nodes  # ty: ignore[unresolved-attribute]
                if not nodes:
                    raise DagsterPlusGraphqlError(f"Asset not found: {asset_key}")
                asset = self._build_asset_from_node(nodes[0])
                if asset is None:
                    raise DagsterPlusGraphqlError(f"Asset not found: {asset_key}")
                return asset
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching asset: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_health(self, asset_key: str) -> DgApiAssetStatus:
        """Get health/status data for a single asset by slash-separated key."""
        asset_key_parts = asset_key.split("/")
        result = self._client.get_asset_health(
            asset_keys=[AssetKeyInput(path=asset_key_parts)],
        ).assets_or_error

        match result.typename__:
            case "AssetConnection":
                nodes = result.nodes  # ty: ignore[unresolved-attribute]
                if not nodes:
                    raise DagsterPlusGraphqlError(f"Asset not found: {asset_key}")
                node = nodes[0]
                return self._build_asset_status(node, asset_key)
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching asset health: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_events(
        self,
        asset_key: str,
        event_type: Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"] | None = None,
        limit: int = 50,
        before: str | None = None,
        partitions: list[str] | None = None,
    ) -> DgApiAssetEventList:
        """Get materialization and/or observation events for an asset.

        Args:
            asset_key: Slash-separated asset key (e.g., 'foo/bar').
            event_type: "ASSET_MATERIALIZATION", "ASSET_OBSERVATION", or None for both.
            limit: Maximum number of events to return (max 1000).
            before: ISO timestamp string for filtering events before this time.
            partitions: List of partition keys to filter by.
        """
        before_timestamp_millis: str | None = None
        if before:
            dt = datetime.datetime.fromisoformat(before)
            before_timestamp_millis = str(int(dt.timestamp() * 1000))

        asset_keys = [AssetKeyInput(path=asset_key.split("/"))]
        events: list[DgApiAssetEvent] = []

        if event_type in ("ASSET_MATERIALIZATION", None):
            mat_result = self._client.get_asset_materialization_events(
                asset_keys=asset_keys,
                limit=limit,
                before_timestamp_millis=before_timestamp_millis,
                partitions=partitions,
            ).assets_or_error

            match mat_result.typename__:
                case "AssetConnection":
                    if not mat_result.nodes:  # ty: ignore[unresolved-attribute]
                        raise DagsterPlusGraphqlError(f"Asset not found: {asset_key}")
                    for mat in mat_result.nodes[0].asset_materializations:  # ty: ignore[unresolved-attribute]
                        events.append(
                            DgApiAssetEvent(
                                timestamp=mat.timestamp,
                                run_id=mat.run_id,
                                event_type="ASSET_MATERIALIZATION",
                                partition=mat.partition,
                                tags=[{"key": t.key, "value": t.value} for t in mat.tags],
                                metadata_entries=[
                                    self._metadata_entry_to_dict(e) for e in mat.metadata_entries
                                ],
                            )
                        )
                case "PythonError":
                    raise DagsterPlusGraphqlError(
                        f"Error fetching asset events: {mat_result.message}"  # ty: ignore[unresolved-attribute]
                    )
                case _ as unreachable:
                    assert_never(unreachable)

        if event_type in ("ASSET_OBSERVATION", None):
            obs_result = self._client.get_asset_observation_events(
                asset_keys=asset_keys,
                limit=limit,
                before_timestamp_millis=before_timestamp_millis,
                partitions=partitions,
            ).assets_or_error

            match obs_result.typename__:
                case "AssetConnection":
                    if not obs_result.nodes:  # ty: ignore[unresolved-attribute]
                        raise DagsterPlusGraphqlError(f"Asset not found: {asset_key}")
                    for obs in obs_result.nodes[0].asset_observations:  # ty: ignore[unresolved-attribute]
                        events.append(
                            DgApiAssetEvent(
                                timestamp=obs.timestamp,
                                run_id=obs.run_id,
                                event_type="ASSET_OBSERVATION",
                                partition=obs.partition,
                                tags=[{"key": t.key, "value": t.value} for t in obs.tags],
                                metadata_entries=[
                                    self._metadata_entry_to_dict(e) for e in obs.metadata_entries
                                ],
                            )
                        )
                case "PythonError":
                    raise DagsterPlusGraphqlError(
                        f"Error fetching asset events: {obs_result.message}"  # ty: ignore[unresolved-attribute]
                    )
                case _ as unreachable:
                    assert_never(unreachable)

        if event_type is None:
            events.sort(key=lambda e: e.timestamp, reverse=True)
            events = events[:limit]

        return DgApiAssetEventList(items=events)

    def get_evaluations(
        self,
        asset_key: str,
        limit: int = 50,
        cursor: str | None = None,
        include_nodes: bool = False,
    ) -> DgApiEvaluationRecordList:
        """Get automation condition evaluation records for an asset.

        Args:
            asset_key: Slash-separated asset key (e.g., 'foo/bar').
            limit: Maximum number of evaluations to return (max 1000).
            cursor: Cursor for pagination (evaluation ID).
            include_nodes: Include the condition evaluation node tree.
        """
        result = self._client.get_asset_condition_evaluations(
            asset_key=AssetKeyInput(path=asset_key.split("/")),
            limit=limit,
            cursor=cursor,
        ).asset_condition_evaluation_records_or_error

        if result is None:
            return DgApiEvaluationRecordList(items=[])

        match result.typename__:
            case "AssetConditionEvaluationRecords":
                records = result.records  # ty: ignore[unresolved-attribute]
                evaluations = [
                    DgApiEvaluationRecord(
                        evaluation_id=int(r.evaluation_id),
                        timestamp=r.timestamp,
                        num_requested=r.num_requested,
                        run_ids=list(r.run_ids),
                        start_timestamp=r.start_timestamp,
                        end_timestamp=r.end_timestamp,
                        root_unique_id=r.root_unique_id,
                        evaluation_nodes=[
                            DgApiEvaluationNode(
                                unique_id=n.unique_id,
                                user_label=n.user_label,
                                expanded_label=list(n.expanded_label),
                                start_timestamp=n.start_timestamp,
                                end_timestamp=n.end_timestamp,
                                num_true=n.num_true,
                                num_candidates=n.num_candidates,
                                is_partitioned=n.is_partitioned,
                                child_unique_ids=list(n.child_unique_ids),
                                operator_type=n.operator_type,
                            )
                            for n in r.evaluation_nodes
                        ]
                        if include_nodes
                        else None,
                    )
                    for r in records
                ]

                return DgApiEvaluationRecordList(items=evaluations)
            case "AutoMaterializeAssetEvaluationNeedsMigrationError":
                raise DagsterPlusGraphqlError(f"Migration required: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_partition_status(self, asset_key: str) -> DgApiPartitionStats:
        """Get partition materialization stats for an asset by slash-separated key."""
        result = self._client.get_asset_partition_status(
            asset_key=AssetKeyInput(path=asset_key.split("/")),
        ).asset_node_or_error

        match result.typename__:
            case "AssetNode":
                partition_stats = result.partition_stats  # ty: ignore[unresolved-attribute]
                if partition_stats is None:
                    raise DagsterPlusGraphqlError("Asset does not have partitions")
                return DgApiPartitionStats(
                    num_materialized=partition_stats.num_materialized,
                    num_failed=partition_stats.num_failed,
                    num_materializing=partition_stats.num_materializing,
                    num_partitions=partition_stats.num_partitions,
                )
            case "AssetNotFoundError":
                raise DagsterPlusGraphqlError(f"Error getting partition status: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _extract_dependency_keys(self, keys_data: list[Any]) -> list[str]:
        """Extract and format dependency keys, filtering out those with slashes in path components.

        Asset keys with slashes in individual path components cannot be represented unambiguously
        in a slash-separated format. For example, ["foo/bar", "baz"] when joined becomes "foo/bar/baz"
        which is indistinguishable from ["foo", "bar", "baz"].
        """
        result = []
        for dep in keys_data:
            path_parts = dep.path
            if any("/" in part for part in path_parts):
                logger.warning(
                    f"Dependency key {path_parts} contains slashes in path components and will not be displayed"
                )
                continue
            result.append("/".join(path_parts))
        return result

    def _metadata_entry_to_dict(self, entry) -> dict:
        d: dict = {"label": entry.label, "description": entry.description or ""}
        match entry.typename__:
            case "BoolMetadataEntry":
                d["boolValue"] = entry.bool_value
            case "FloatMetadataEntry":
                d["floatValue"] = entry.float_value
            case "IntMetadataEntry":
                d["intValue"] = entry.int_value
            case "JsonMetadataEntry":
                d["jsonString"] = entry.json_string
            case "MarkdownMetadataEntry":
                d["mdStr"] = entry.md_str
            case "PathMetadataEntry":
                d["path"] = entry.path
            case "PythonArtifactMetadataEntry":
                d["module"] = entry.module
                d["name"] = entry.name
            case "TextMetadataEntry":
                d["text"] = entry.text
            case "UrlMetadataEntry":
                d["url"] = entry.url

        return d

    def _build_asset_from_node(
        self,
        node: GetAssetDetailsAssetsOrErrorAssetConnectionNodes,
    ) -> DgApiAsset | None:
        """Build a DgApiAsset from an assetsOrError node.

        Returns None if the node's definition is null (asset doesn't exist in code).
        """
        definition = node.definition
        if definition is None:
            return None

        asset_key_parts = node.key.path
        asset_key = "/".join(asset_key_parts)

        metadata_entries = [self._metadata_entry_to_dict(e) for e in definition.metadata_entries]
        dependency_keys = self._extract_dependency_keys(definition.dependency_keys)

        automation_condition = None
        if definition.automation_condition:
            ac = definition.automation_condition
            automation_condition = DgApiAutomationCondition(
                label=ac.label,
                expanded_label=ac.expanded_label,
            )

        partition_definition = None
        if definition.partition_definition:
            partition_definition = DgApiPartitionDefinition(
                description=definition.partition_definition.description,
            )

        upstream_dependencies: list[DgApiAssetDependency] | None = None
        if definition.dependencies:
            upstream_dependencies = []
            for dep in definition.dependencies:
                dep_key_parts = dep.asset.asset_key.path
                partition_mapping = None
                if dep.partition_mapping:
                    partition_mapping = DgApiPartitionMapping(
                        class_name=dep.partition_mapping.class_name,
                        description=dep.partition_mapping.description,
                    )
                upstream_dependencies.append(
                    DgApiAssetDependency(
                        asset_key="/".join(dep_key_parts),
                        partition_mapping=partition_mapping,
                    )
                )

        downstream_keys: list[str] | None = None
        if definition.depended_by_keys:
            downstream_keys = self._extract_dependency_keys(definition.depended_by_keys)

        owners: list[dict] | None = None
        if definition.owners:
            owners = []
            for owner in definition.owners:
                match owner.typename__:
                    case "UserAssetOwner":
                        owners.append({"email": owner.email})  # ty: ignore[unresolved-attribute]
                    case "TeamAssetOwner":
                        owners.append({"team": owner.team})  # ty: ignore[unresolved-attribute]

        tags: list[dict] | None = None
        if definition.tags:
            tags = [{"key": t.key, "value": t.value} for t in definition.tags]

        backfill_policy = None
        if definition.backfill_policy:
            backfill_policy = DgApiBackfillPolicy(
                max_partitions_per_run=definition.backfill_policy.max_partitions_per_run,
            )

        job_names = definition.job_names if definition.job_names else None

        return DgApiAsset(
            id=node.id,
            asset_key=asset_key,
            asset_key_parts=asset_key_parts,
            description=definition.description,
            group_name=definition.group_name,
            kinds=list(definition.kinds),
            metadata_entries=metadata_entries,
            dependency_keys=dependency_keys,
            automation_condition=automation_condition,
            partition_definition=partition_definition,
            upstream_dependencies=upstream_dependencies,
            downstream_keys=downstream_keys,
            owners=owners,
            tags=tags,
            backfill_policy=backfill_policy,
            job_names=job_names,
        )

    def _build_asset_status(
        self, node: GetAssetHealthAssetsOrErrorAssetConnectionNodes, asset_key: str
    ) -> DgApiAssetStatus:
        asset_health_data = node.asset_health
        if asset_health_data is None:
            return DgApiAssetStatus(
                asset_key=asset_key,
                asset_health=None,
                materialization_status=None,
                freshness_status=None,
                asset_checks_status=None,
                health_metadata=None,
                latest_materialization=None,
                freshness_info=None,
                checks_status=None,
            )

        freshness_info = None

        if asset_health_data.freshness_status_metadata:
            # none of these are available in status metadata
            # existing logic implied the different freshness
            # categories are mutually exclusive
            freshness_info = DgApiAssetFreshnessInfo(
                current_lag_minutes=None,
                current_minutes_late=None,
                latest_materialization_minutes_late=None,
                maximum_lag_minutes=None,
                cron_schedule=None,
            )

        if not freshness_info:
            definition_data = node.definition
            if definition_data:
                freshness_data = definition_data.freshness_info
                freshness_policy = definition_data.freshness_policy
                if freshness_data or freshness_policy:
                    freshness_info = DgApiAssetFreshnessInfo(
                        current_lag_minutes=freshness_data.current_lag_minutes
                        if freshness_data
                        else None,
                        current_minutes_late=freshness_data.current_minutes_late
                        if freshness_data
                        else None,
                        latest_materialization_minutes_late=freshness_data.latest_materialization_minutes_late
                        if freshness_data
                        else None,
                        maximum_lag_minutes=freshness_policy.maximum_lag_minutes
                        if freshness_policy
                        else None,
                        cron_schedule=freshness_policy.cron_schedule if freshness_policy else None,
                    )

        latest_materialization = None
        if node.asset_materializations:
            latest = node.asset_materializations[0]
            latest_materialization = DgApiAssetMaterialization(
                timestamp=float(latest.timestamp) if latest.timestamp else None,
                run_id=latest.run_id,
                partition=latest.partition,
            )

        checks_status = DgApiAssetChecksStatus(
            status=asset_health_data.asset_checks_status,
            num_failed_checks=None,
            num_warning_checks=None,
            total_num_checks=None,
        )
        if asset_health_data.asset_checks_status_metadata:
            checks_metadata = asset_health_data.asset_checks_status_metadata
            if checks_metadata:
                match checks_metadata.typename__:
                    case "AssetHealthCheckDegradedMeta":
                        checks_status.num_failed_checks = checks_metadata.num_failed_checks  # ty: ignore[unresolved-attribute]
                        checks_status.num_warning_checks = checks_metadata.num_warning_checks  # ty: ignore[unresolved-attribute]
                        checks_status.total_num_checks = checks_metadata.total_num_checks
                    case "AssetHealthCheckWarningMeta":
                        checks_status.num_warning_checks = checks_metadata.num_warning_checks  # ty: ignore[unresolved-attribute]
                        checks_status.total_num_checks = checks_metadata.total_num_checks
                    case "AssetHealthCheckUnknownMeta":
                        checks_status.total_num_checks = checks_metadata.total_num_checks
                    case _ as unreachable:
                        assert_never(unreachable)

        return DgApiAssetStatus(
            asset_key=asset_key,
            asset_health=asset_health_data.asset_health,
            materialization_status=asset_health_data.materialization_status,
            freshness_status=asset_health_data.freshness_status,
            asset_checks_status=asset_health_data.asset_checks_status,
            health_metadata=None,
            latest_materialization=latest_materialization,
            freshness_info=freshness_info,
            checks_status=checks_status,
        )
