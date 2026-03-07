"""GraphQL implementation for asset operations."""

import logging

from dagster_dg_cli.api_layer.schemas.asset import (
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
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

logger = logging.getLogger(__name__)


def _extract_dependency_keys(dependency_keys_data: list[dict]) -> list[str]:
    """Extract and format dependency keys, filtering out those with slashes in path components.

    Asset keys with slashes in individual path components cannot be represented unambiguously
    in a slash-separated format. For example, ["foo/bar", "baz"] when joined becomes "foo/bar/baz"
    which is indistinguishable from ["foo", "bar", "baz"].
    """
    dependency_keys = []
    for dep in dependency_keys_data:
        path_parts = dep["path"]
        # Check if any path component contains a slash
        if any("/" in part for part in path_parts):
            # Skip this dependency - can't represent it unambiguously in slash-separated format
            logger.warning(
                f"Dependency key {path_parts} contains slashes in path components and will not be displayed"
            )
            continue
        dependency_keys.append("/".join(path_parts))
    return dependency_keys


# Shared GraphQL fragment for metadata entries
METADATA_ENTRIES_FRAGMENT = """
    metadataEntries {
        label
        description
        ... on TextMetadataEntry { text }
        ... on UrlMetadataEntry { url }
        ... on PathMetadataEntry { path }
        ... on JsonMetadataEntry { jsonString }
        ... on MarkdownMetadataEntry { mdStr }
        ... on PythonArtifactMetadataEntry { module name }
        ... on FloatMetadataEntry { floatValue }
        ... on IntMetadataEntry { intValue }
        ... on BoolMetadataEntry { boolValue }
    }
"""

_METADATA_VALUE_FIELDS = [
    "text",
    "url",
    "path",
    "jsonString",
    "mdStr",
    "floatValue",
    "intValue",
    "boolValue",
]


def _parse_metadata_entries(raw_entries: list[dict]) -> list[dict]:
    """Parse raw GraphQL metadata entries into a normalized dict format."""
    metadata_entries = []
    for entry in raw_entries:
        metadata_dict: dict = {
            "label": entry.get("label", ""),
            "description": entry.get("description", ""),
        }
        for field in _METADATA_VALUE_FIELDS:
            if field in entry:
                metadata_dict[field] = entry[field]
        if "module" in entry and "name" in entry:
            metadata_dict["module"] = entry["module"]
            metadata_dict["name"] = entry["name"]
        metadata_entries.append(metadata_dict)
    return metadata_entries


def _build_asset_from_node(node_data: dict, include_status: bool) -> DgApiAsset | None:
    """Build a DgApiAsset from an assetsOrError node.

    Returns None if the node's definition is null (asset doesn't exist in code).
    """
    definition = node_data.get("definition")
    if definition is None:
        return None

    asset_key_parts = node_data["key"]["path"]
    asset_key = "/".join(asset_key_parts)

    metadata_entries = _parse_metadata_entries(definition.get("metadataEntries", []))
    dependency_keys = _extract_dependency_keys(definition.get("dependencyKeys", []))

    status = _transform_asset_status_data(node_data) if include_status else None

    extended_kwargs = _extract_extended_asset_details(definition)

    return DgApiAsset(
        id=node_data["id"],
        asset_key=asset_key,
        asset_key_parts=asset_key_parts,
        description=definition.get("description"),
        group_name=definition.get("groupName", ""),
        kinds=definition.get("kinds", []),
        metadata_entries=metadata_entries,
        dependency_keys=dependency_keys,
        status=status,
        **extended_kwargs,
    )


# GraphQL queries

ASSET_RECORDS_QUERY = """
query AssetRecords($cursor: String, $limit: Int) {
    assetRecordsOrError(cursor: $cursor, limit: $limit) {
        __typename
        ... on AssetRecordConnection {
            assets {
                id
                key {
                    path
                }
            }
            cursor
        }
        ... on PythonError {
            message
        }
    }
}
"""

EXTENDED_DEFINITION_FIELDS = """
                    # Automation
                    automationCondition {
                        label
                        expandedLabel
                    }
                    # Partitions
                    partitionDefinition {
                        description
                    }
                    # Dependencies with partition mappings
                    dependencies {
                        asset { assetKey { path } }
                        partitionMapping { className description }
                    }
                    dependedByKeys { path }
                    # Additional detail fields
                    owners {
                        ... on UserAssetOwner { email }
                        ... on TeamAssetOwner { team }
                    }
                    tags { key value }
                    backfillPolicy {
                        maxPartitionsPerRun
                    }
                    jobNames
"""

ASSET_DETAIL_QUERY = (
    """
query AssetDetail($assetKeys: [AssetKeyInput!]!) {
    assetsOrError(assetKeys: $assetKeys) {
        __typename
        ... on AssetConnection {
            nodes {
                id
                key { path }
                definition {
                    description
                    groupName
                    kinds
                    dependencyKeys { path }
"""
    + METADATA_ENTRIES_FRAGMENT
    + EXTENDED_DEFINITION_FIELDS
    + """
                }
            }
        }
        ... on PythonError {
            message
        }
    }
}
"""
)

ASSETS_WITH_STATUS_QUERY = (
    """
query AssetsWithStatus($assetKeys: [AssetKeyInput!]!) {
    assetsOrError(assetKeys: $assetKeys) {
        __typename
        ... on AssetConnection {
            nodes {
                id
                key { path }
                # Asset definition contains the metadata, description, etc.
                definition {
                    description
                    groupName
                    kinds
                    dependencyKeys {
                        path
                    }
"""
    + METADATA_ENTRIES_FRAGMENT
    + EXTENDED_DEFINITION_FIELDS
    + """
                    # Freshness information from definition
                    freshnessInfo {
                        currentLagMinutes
                        currentMinutesLate
                        latestMaterializationMinutesLate
                    }
                    freshnessPolicy {
                        maximumLagMinutes
                        cronSchedule
                    }
                }
                # Asset health status information - this is the key missing data
                assetHealth {
                    assetHealth
                    materializationStatus
                    materializationStatusMetadata {
                        ... on AssetHealthMaterializationDegradedPartitionedMeta {
                            numMissingPartitions
                            numFailedPartitions
                            totalNumPartitions
                        }
                        ... on AssetHealthMaterializationHealthyPartitionedMeta {
                            numMissingPartitions
                            totalNumPartitions
                        }
                        ... on AssetHealthMaterializationDegradedNotPartitionedMeta {
                            failedRunId
                        }
                    }
                    assetChecksStatus
                    assetChecksStatusMetadata {
                        ... on AssetHealthCheckDegradedMeta {
                            numFailedChecks
                            numWarningChecks
                            totalNumChecks
                        }
                        ... on AssetHealthCheckWarningMeta {
                            numWarningChecks
                            totalNumChecks
                        }
                        ... on AssetHealthCheckUnknownMeta {
                            numNotExecutedChecks
                            totalNumChecks
                        }
                    }
                    freshnessStatus
                    freshnessStatusMetadata {
                        lastMaterializedTimestamp
                    }
                }
                # Latest materialization information
                assetMaterializations(limit: 1) {
                    timestamp
                    runId
                    partition
                }
            }
        }
        ... on PythonError {
            message
        }
    }
}
"""
)


def _extract_extended_asset_details(definition: dict) -> dict:
    """Extract extended detail fields from a definition node.

    Returns a dict of kwargs to pass to DgApiAsset constructor.
    """
    result: dict = {}

    # Automation condition
    ac_data = definition.get("automationCondition")
    if ac_data:
        result["automation_condition"] = DgApiAutomationCondition(
            label=ac_data.get("label"),
            expanded_label=ac_data.get("expandedLabel", []),
        )

    # Partition definition
    pd_data = definition.get("partitionDefinition")
    if pd_data:
        result["partition_definition"] = DgApiPartitionDefinition(
            description=pd_data["description"],
        )

    # Upstream dependencies with partition mappings
    deps_data = definition.get("dependencies", [])
    if deps_data:
        upstream_deps = []
        for dep in deps_data:
            dep_key_parts = dep["asset"]["assetKey"]["path"]
            pm_data = dep.get("partitionMapping")
            partition_mapping = None
            if pm_data:
                partition_mapping = DgApiPartitionMapping(
                    class_name=pm_data["className"],
                    description=pm_data["description"],
                )
            upstream_deps.append(
                DgApiAssetDependency(
                    asset_key="/".join(dep_key_parts),
                    partition_mapping=partition_mapping,
                )
            )
        result["upstream_dependencies"] = upstream_deps

    # Downstream keys
    depended_by_keys = definition.get("dependedByKeys", [])
    if depended_by_keys:
        result["downstream_keys"] = _extract_dependency_keys(depended_by_keys)

    # Owners
    owners_data = definition.get("owners", [])
    if owners_data:
        result["owners"] = owners_data

    # Tags
    tags_data = definition.get("tags", [])
    if tags_data:
        result["tags"] = [{"key": t["key"], "value": t["value"]} for t in tags_data]

    # Backfill policy
    bp_data = definition.get("backfillPolicy")
    if bp_data:
        result["backfill_policy"] = DgApiBackfillPolicy(
            max_partitions_per_run=bp_data.get("maxPartitionsPerRun"),
        )

    # Job names
    job_names = definition.get("jobNames", [])
    if job_names:
        result["job_names"] = job_names

    return result


def _transform_asset_status_data(asset_data) -> DgApiAssetStatus:
    """Transform GraphQL asset data (from assetsOrError) into status format."""
    if not asset_data:
        return DgApiAssetStatus(
            asset_health=None,
            materialization_status=None,
            freshness_status=None,
            asset_checks_status=None,
            health_metadata=None,
            latest_materialization=None,
            freshness_info=None,
            checks_status=None,
        )

    # Extract asset health data - this is now available from assetsOrError query
    asset_health_data = asset_data.get("assetHealth", {})

    # Extract status values from assetHealth
    asset_health = asset_health_data.get("assetHealth")
    materialization_status = asset_health_data.get("materializationStatus")
    freshness_status = asset_health_data.get("freshnessStatus")
    asset_checks_status = asset_health_data.get("assetChecksStatus")

    # Extract freshness info from both sources
    freshness_info = None

    # Try freshness status metadata first (from assetHealth)
    freshness_status_metadata = asset_health_data.get("freshnessStatusMetadata", {})
    if freshness_status_metadata:
        freshness_info = DgApiAssetFreshnessInfo(
            current_lag_minutes=None,  # Not available in status metadata
            current_minutes_late=None,  # Not available in status metadata
            latest_materialization_minutes_late=None,  # Not available in status metadata
            maximum_lag_minutes=None,  # Not available in status metadata
            cron_schedule=None,  # Not available in status metadata
        )

    # Fall back to freshnessInfo and freshnessPolicy for compatibility
    if not freshness_info:
        definition_data = asset_data.get("definition") or {}
        freshness_data = definition_data.get("freshnessInfo", {})
        freshness_policy = definition_data.get("freshnessPolicy", {})
        if freshness_data or freshness_policy:
            freshness_info = DgApiAssetFreshnessInfo(
                current_lag_minutes=freshness_data.get("currentLagMinutes"),
                current_minutes_late=freshness_data.get("currentMinutesLate"),
                latest_materialization_minutes_late=freshness_data.get(
                    "latestMaterializationMinutesLate"
                ),
                maximum_lag_minutes=freshness_policy.get("maximumLagMinutes"),
                cron_schedule=freshness_policy.get("cronSchedule"),
            )

    # Extract latest materialization from assetMaterializations
    latest_materialization = None
    mat_events = asset_data.get("assetMaterializations", [])
    if mat_events:
        latest = mat_events[0]  # Already limited to 1 in query
        latest_materialization = DgApiAssetMaterialization(
            timestamp=latest.get("timestamp"),
            run_id=latest.get("runId"),
            partition=latest.get("partition"),
        )

    # Create checks status object from raw status and metadata
    checks_status = None
    if asset_checks_status:
        # Extract check metadata if available
        checks_metadata = asset_health_data.get("assetChecksStatusMetadata") or {}
        checks_status = DgApiAssetChecksStatus(
            status=asset_checks_status,
            num_failed_checks=checks_metadata.get("numFailedChecks"),
            num_warning_checks=checks_metadata.get("numWarningChecks"),
            total_num_checks=checks_metadata.get("totalNumChecks"),
        )

    # Return status with actual health data
    return DgApiAssetStatus(
        asset_health=asset_health,
        materialization_status=materialization_status,
        freshness_status=freshness_status,
        asset_checks_status=asset_checks_status,
        health_metadata=None,  # Could be populated from status metadata if needed
        latest_materialization=latest_materialization,
        freshness_info=freshness_info,
        checks_status=checks_status,
    )


def _fetch_assets_or_error(
    client: IGraphQLClient,
    query: str,
    asset_keys: list[dict],
) -> list[dict]:
    """Execute an assetsOrError query and return the nodes list."""
    result = client.execute(query, variables={"assetKeys": asset_keys})
    assets_or_error = result.get("assetsOrError", {})
    if assets_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {assets_or_error.get('message', 'Unknown error')}")
    return assets_or_error.get("nodes", [])


def list_dg_plus_api_assets_via_graphql(
    client: IGraphQLClient,
    limit: int | None = None,
    cursor: str | None = None,
    status: bool = False,
) -> DgApiAssetList:
    """Fetch assets using two-step GraphQL approach.

    1. Use assetRecordsOrError for paginated asset keys
    2. Use assetsOrError to fetch metadata (and optionally status) for those keys
    3. Combine and transform data
    """
    # Step 1: Get paginated asset keys
    variables = {}
    if cursor:
        variables["cursor"] = cursor
    if limit is not None:
        variables["limit"] = limit

    result = client.execute(ASSET_RECORDS_QUERY, variables=variables)

    asset_records_or_error = result.get("assetRecordsOrError", {})
    if asset_records_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {asset_records_or_error.get('message', 'Unknown error')}")

    records = asset_records_or_error.get("assets", [])
    next_cursor = asset_records_or_error.get("cursor")

    if not records:
        return DgApiAssetList(items=[], cursor=None, has_more=False)

    # Step 2: Get detailed metadata (and optionally status) for these asset keys
    asset_keys = [{"path": record["key"]["path"]} for record in records]
    query = ASSETS_WITH_STATUS_QUERY if status else ASSET_DETAIL_QUERY
    asset_nodes = _fetch_assets_or_error(client, query, asset_keys)

    # Step 3: Transform and combine data
    assets = []
    nodes_by_key = {"/".join(node["key"]["path"]): node for node in asset_nodes}

    for record in records:
        asset_key_parts = record["key"]["path"]
        asset_key = "/".join(asset_key_parts)
        node_data = nodes_by_key.get(asset_key)
        if not node_data:
            continue
        asset = _build_asset_from_node(node_data, include_status=status)
        if asset is not None:
            assets.append(asset)

    has_more = next_cursor is not None

    return DgApiAssetList(
        items=assets,
        cursor=next_cursor,
        has_more=has_more,
    )


def get_dg_plus_api_asset_via_graphql(
    client: IGraphQLClient,
    asset_key_parts: list[str],
    status: bool = False,
) -> DgApiAsset:
    """Single asset fetch using assetsOrError with specific assetKey."""
    query = ASSETS_WITH_STATUS_QUERY if status else ASSET_DETAIL_QUERY
    asset_nodes = _fetch_assets_or_error(client, query, [{"path": asset_key_parts}])

    if not asset_nodes:
        raise Exception(f"Asset not found: {'/'.join(asset_key_parts)}")

    node = asset_nodes[0]
    asset = _build_asset_from_node(node, include_status=status)
    if asset is None:
        raise Exception(f"Asset not found: {'/'.join(asset_key_parts)}")

    return asset


def _build_asset_events_query(event_type: str | None) -> str:
    """Build the GraphQL query for asset events based on requested event type.

    Args:
        event_type: "ASSET_MATERIALIZATION", "ASSET_OBSERVATION", or None for both.
    """
    event_fields = f"""
                    timestamp
                    runId
                    partition
                    tags {{ key value }}
                    {METADATA_ENTRIES_FRAGMENT}"""

    materializations_fragment = f"""
                assetMaterializations(limit: $limit, beforeTimestampMillis: $beforeTimestampMillis, partitions: $partitions) {{{event_fields}
                }}"""

    observations_fragment = f"""
                assetObservations(limit: $limit, beforeTimestampMillis: $beforeTimestampMillis, partitions: $partitions) {{{event_fields}
                }}"""

    if event_type == "ASSET_MATERIALIZATION":
        event_fragments = materializations_fragment
    elif event_type == "ASSET_OBSERVATION":
        event_fragments = observations_fragment
    else:
        event_fragments = materializations_fragment + observations_fragment

    return f"""
query AssetEvents($assetKeys: [AssetKeyInput!]!, $limit: Int, $beforeTimestampMillis: String, $partitions: [String!]) {{
    assetsOrError(assetKeys: $assetKeys) {{
        __typename
        ... on AssetConnection {{
            nodes {{
                key {{ path }}{event_fragments}
            }}
        }}
        ... on PythonError {{ message }}
    }}
}}
"""


def get_asset_events_via_graphql(
    client: IGraphQLClient,
    asset_key: str,
    event_type: str | None = None,
    limit: int = 50,
    before_timestamp_millis: str | None = None,
    partitions: list[str] | None = None,
) -> DgApiAssetEventList:
    """Fetch materialization and/or observation events for an asset."""
    asset_key_parts = asset_key.split("/")
    query = _build_asset_events_query(event_type)

    variables: dict = {"assetKeys": [{"path": asset_key_parts}]}
    if before_timestamp_millis:
        variables["beforeTimestampMillis"] = before_timestamp_millis
    if partitions:
        variables["partitions"] = partitions

    variables["limit"] = limit

    result = client.execute(query, variables=variables)
    assets_or_error = result.get("assetsOrError", {})
    if assets_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {assets_or_error.get('message', 'Unknown error')}")

    nodes = assets_or_error.get("nodes", [])

    if not nodes:
        raise Exception(f"Asset not found: {asset_key}")

    node = nodes[0]
    events: list[DgApiAssetEvent] = []

    # Process materializations
    if event_type in ("ASSET_MATERIALIZATION", None):
        for mat in node.get("assetMaterializations", []):
            events.append(
                DgApiAssetEvent(
                    timestamp=mat["timestamp"],
                    run_id=mat["runId"],
                    event_type="ASSET_MATERIALIZATION",
                    partition=mat.get("partition"),
                    tags=[{"key": t["key"], "value": t["value"]} for t in mat.get("tags", [])],
                    metadata_entries=_parse_metadata_entries(mat.get("metadataEntries", [])),
                )
            )

    # Process observations
    if event_type in ("ASSET_OBSERVATION", None):
        for obs in node.get("assetObservations", []):
            events.append(
                DgApiAssetEvent(
                    timestamp=obs["timestamp"],
                    run_id=obs["runId"],
                    event_type="ASSET_OBSERVATION",
                    partition=obs.get("partition"),
                    tags=[{"key": t["key"], "value": t["value"]} for t in obs.get("tags", [])],
                    metadata_entries=_parse_metadata_entries(obs.get("metadataEntries", [])),
                )
            )

    # Sort by timestamp descending (newest first) and apply limit when merging both types
    if event_type is None:
        events.sort(key=lambda e: e.timestamp, reverse=True)
        events = events[:limit]

    return DgApiAssetEventList(items=events)


ASSET_CONDITION_EVALUATIONS_QUERY = """
query AssetConditionEvaluations($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    assetConditionEvaluationRecordsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
        __typename
        ... on AssetConditionEvaluationRecords {
            records {
                evaluationId
                timestamp
                numRequested
                runIds
                startTimestamp
                endTimestamp
                rootUniqueId
                evaluationNodes {
                    uniqueId
                    userLabel
                    expandedLabel
                    startTimestamp
                    endTimestamp
                    numTrue
                    numCandidates
                    isPartitioned
                    childUniqueIds
                    operatorType
                }
            }
        }
        ... on AutoMaterializeAssetEvaluationNeedsMigrationError {
            message
        }
    }
}
"""


def get_asset_evaluations_via_graphql(
    client: IGraphQLClient,
    asset_key: str,
    limit: int = 50,
    cursor: str | None = None,
    include_nodes: bool = False,
) -> DgApiEvaluationRecordList:
    """Fetch automation condition evaluation records for an asset."""
    asset_key_parts = asset_key.split("/")
    variables: dict = {
        "assetKey": {"path": asset_key_parts},
        "limit": limit,
    }
    if cursor:
        variables["cursor"] = cursor

    result = client.execute(ASSET_CONDITION_EVALUATIONS_QUERY, variables=variables)
    records_or_error = result.get("assetConditionEvaluationRecordsOrError", {})

    if records_or_error.get("__typename") == "AutoMaterializeAssetEvaluationNeedsMigrationError":
        raise Exception(f"Migration required: {records_or_error.get('message', 'Unknown error')}")

    raw_records = records_or_error.get("records", [])
    evaluations: list[DgApiEvaluationRecord] = []

    for raw in raw_records:
        nodes: list[DgApiEvaluationNode] | None = None
        if include_nodes:
            nodes = [
                DgApiEvaluationNode(
                    unique_id=n["uniqueId"],
                    user_label=n.get("userLabel"),
                    expanded_label=n.get("expandedLabel", []),
                    start_timestamp=n.get("startTimestamp"),
                    end_timestamp=n.get("endTimestamp"),
                    num_true=n.get("numTrue"),
                    num_candidates=n.get("numCandidates"),
                    is_partitioned=n["isPartitioned"],
                    child_unique_ids=n.get("childUniqueIds", []),
                    operator_type=n["operatorType"],
                )
                for n in raw.get("evaluationNodes", [])
            ]

        evaluations.append(
            DgApiEvaluationRecord(
                evaluation_id=int(raw["evaluationId"]),
                timestamp=raw["timestamp"],
                num_requested=raw.get("numRequested"),
                run_ids=raw.get("runIds", []),
                start_timestamp=raw.get("startTimestamp"),
                end_timestamp=raw.get("endTimestamp"),
                root_unique_id=raw["rootUniqueId"],
                evaluation_nodes=nodes,
            )
        )

    return DgApiEvaluationRecordList(items=evaluations)
