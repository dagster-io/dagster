"""GraphQL implementation for asset operations."""

import logging
from typing import Optional

from dagster_dg_cli.api_layer.schemas.asset import (
    DgApiAsset,
    DgApiAssetChecksStatus,
    DgApiAssetFreshnessInfo,
    DgApiAssetList,
    DgApiAssetMaterialization,
    DgApiAssetStatus,
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

ASSET_NODES_QUERY = """
query AssetNodes($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
        id
        assetKey {
            path
        }
        description
        groupName
        kinds
        dependencyKeys {
            path
        }
        metadataEntries {
            label
            description
            ... on TextMetadataEntry {
                text
            }
            ... on UrlMetadataEntry {
                url
            }
            ... on PathMetadataEntry {
                path
            }
            ... on JsonMetadataEntry {
                jsonString
            }
            ... on MarkdownMetadataEntry {
                mdStr
            }
            ... on PythonArtifactMetadataEntry {
                module
                name
            }
            ... on FloatMetadataEntry {
                floatValue
            }
            ... on IntMetadataEntry {
                intValue
            }
            ... on BoolMetadataEntry {
                boolValue
            }
        }
    }
}
"""


def list_dg_plus_api_assets_via_graphql(
    client: IGraphQLClient,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> DgApiAssetList:
    """Fetch assets using two-step GraphQL approach.

    1. Use assetRecordsOrError for paginated asset keys
    2. Use assetNodes to fetch metadata for those keys
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

    # Step 2: Get detailed metadata for these asset keys
    asset_keys = [{"path": record["key"]["path"]} for record in records]

    nodes_result = client.execute(ASSET_NODES_QUERY, variables={"assetKeys": asset_keys})
    asset_nodes = nodes_result.get("assetNodes", [])

    # Step 3: Transform and combine data
    assets = []
    for node in asset_nodes:
        asset_key_parts = node["assetKey"]["path"]
        asset_key = "/".join(asset_key_parts)

        # Convert metadata entries to dict format
        metadata_entries = []
        for entry in node.get("metadataEntries", []):
            metadata_dict = {
                "label": entry.get("label", ""),
                "description": entry.get("description", ""),
            }

            # Add type-specific fields
            if "text" in entry:
                metadata_dict["text"] = entry["text"]
            elif "url" in entry:
                metadata_dict["url"] = entry["url"]
            elif "path" in entry:
                metadata_dict["path"] = entry["path"]
            elif "jsonString" in entry:
                metadata_dict["jsonString"] = entry["jsonString"]
            elif "mdStr" in entry:
                metadata_dict["mdStr"] = entry["mdStr"]
            elif "module" in entry and "name" in entry:
                metadata_dict["module"] = entry["module"]
                metadata_dict["name"] = entry["name"]
            elif "floatValue" in entry:
                metadata_dict["floatValue"] = entry["floatValue"]
            elif "intValue" in entry:
                metadata_dict["intValue"] = entry["intValue"]
            elif "boolValue" in entry:
                metadata_dict["boolValue"] = entry["boolValue"]

            metadata_entries.append(metadata_dict)

        # Extract dependency keys
        dependency_keys = _extract_dependency_keys(node.get("dependencyKeys", []))

        asset = DgApiAsset(
            id=node["id"],
            asset_key=asset_key,
            asset_key_parts=asset_key_parts,
            description=node.get("description"),
            group_name=node.get("groupName", ""),
            kinds=node.get("kinds", []),
            metadata_entries=metadata_entries,
            dependency_keys=dependency_keys,
        )
        assets.append(asset)

    # Determine if there are more results
    has_more = next_cursor is not None

    return DgApiAssetList(
        items=assets,
        cursor=next_cursor,
        has_more=has_more,
    )


def get_dg_plus_api_asset_via_graphql(
    client: IGraphQLClient, asset_key_parts: list[str]
) -> DgApiAsset:
    """Single asset fetch using assetNodes with specific assetKey."""
    variables = {"assetKeys": [{"path": asset_key_parts}]}

    result = client.execute(ASSET_NODES_QUERY, variables=variables)
    asset_nodes = result.get("assetNodes", [])

    if not asset_nodes:
        raise Exception(f"Asset not found: {'/'.join(asset_key_parts)}")

    node = asset_nodes[0]
    asset_key = "/".join(asset_key_parts)

    # Convert metadata entries to dict format
    metadata_entries = []
    for entry in node.get("metadataEntries", []):
        metadata_dict = {
            "label": entry.get("label", ""),
            "description": entry.get("description", ""),
        }

        # Add type-specific fields
        if "text" in entry:
            metadata_dict["text"] = entry["text"]
        elif "url" in entry:
            metadata_dict["url"] = entry["url"]
        elif "path" in entry:
            metadata_dict["path"] = entry["path"]
        elif "jsonString" in entry:
            metadata_dict["jsonString"] = entry["jsonString"]
        elif "mdStr" in entry:
            metadata_dict["mdStr"] = entry["mdStr"]
        elif "module" in entry and "name" in entry:
            metadata_dict["module"] = entry["module"]
            metadata_dict["name"] = entry["name"]
        elif "floatValue" in entry:
            metadata_dict["floatValue"] = entry["floatValue"]
        elif "intValue" in entry:
            metadata_dict["intValue"] = entry["intValue"]
        elif "boolValue" in entry:
            metadata_dict["boolValue"] = entry["boolValue"]

        metadata_entries.append(metadata_dict)

    # Extract dependency keys
    dependency_keys = _extract_dependency_keys(node.get("dependencyKeys", []))

    return DgApiAsset(
        id=node["id"],
        asset_key=asset_key,
        asset_key_parts=asset_key_parts,
        description=node.get("description"),
        group_name=node.get("groupName", ""),
        kinds=node.get("kinds", []),
        metadata_entries=metadata_entries,
        dependency_keys=dependency_keys,
    )


# Status view GraphQL queries - using assetsOrError to get assetHealth data
ASSETS_WITH_STATUS_QUERY = """
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

ASSET_RECORDS_WITH_STATUS_QUERY = """
query AssetRecordsWithStatus($cursor: String, $limit: Int) {
    assetRecordsOrError(cursor: $cursor, limit: $limit) {
        __typename
        ... on AssetRecordConnection {
            assets {
                id
                key { path }
            }
            cursor
        }
        ... on PythonError {
            message
        }
    }
}
"""


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


def list_dg_plus_api_assets_with_status_via_graphql(
    client: IGraphQLClient,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> DgApiAssetList:
    """Fetch assets with status information using comprehensive GraphQL approach."""
    # Step 1: Get paginated asset keys
    variables = {}
    if cursor:
        variables["cursor"] = cursor
    if limit is not None:
        variables["limit"] = limit

    result = client.execute(ASSET_RECORDS_WITH_STATUS_QUERY, variables=variables)

    asset_records_or_error = result.get("assetRecordsOrError", {})
    if asset_records_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {asset_records_or_error.get('message', 'Unknown error')}")

    records = asset_records_or_error.get("assets", [])
    next_cursor = asset_records_or_error.get("cursor")

    if not records:
        return DgApiAssetList(items=[], cursor=None, has_more=False)

    # Step 2: Get comprehensive status data for these asset keys
    asset_keys = [{"path": record["key"]["path"]} for record in records]

    status_result = client.execute(ASSETS_WITH_STATUS_QUERY, variables={"assetKeys": asset_keys})

    # Handle assetsOrError response structure
    assets_or_error = status_result.get("assetsOrError", {})
    if assets_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {assets_or_error.get('message', 'Unknown error')}")

    asset_nodes = assets_or_error.get("nodes", [])

    # Step 3: Transform and combine data
    assets = []

    # Create lookup map for efficient merging
    nodes_by_key = {"/".join(node["key"]["path"]): node for node in asset_nodes}

    for record in records:
        asset_key_parts = record["key"]["path"]
        asset_key = "/".join(asset_key_parts)

        # There will always be a node since we queried for these keys specifically, but the
        # definition may be null if the asset does not exist.
        node_data = nodes_by_key[asset_key]
        if not node_data.get("definition"):
            continue  # Skip if we don't have node data

        # Build basic asset data from definition
        definition_data = node_data.get("definition", {})
        metadata_entries = []
        for entry in definition_data.get("metadataEntries", []):
            metadata_dict = {
                "label": entry.get("label", ""),
                "description": entry.get("description", ""),
            }

            # Add type-specific fields (same logic as existing)
            for field in [
                "text",
                "url",
                "path",
                "jsonString",
                "mdStr",
                "floatValue",
                "intValue",
                "boolValue",
            ]:
                if field in entry:
                    metadata_dict[field] = entry[field]
            if "module" in entry and "name" in entry:
                metadata_dict.update({"module": entry["module"], "name": entry["name"]})

            metadata_entries.append(metadata_dict)

        # Extract dependency keys
        dependency_keys = _extract_dependency_keys(definition_data.get("dependencyKeys", []))

        # Build status data
        status = _transform_asset_status_data(node_data)

        asset = DgApiAsset(
            id=node_data["id"],
            asset_key=asset_key,
            asset_key_parts=asset_key_parts,
            description=definition_data.get("description"),
            group_name=definition_data.get("groupName", ""),
            kinds=definition_data.get("kinds", []),
            metadata_entries=metadata_entries,
            dependency_keys=dependency_keys,
            status=status,
        )
        assets.append(asset)

    has_more = next_cursor is not None

    return DgApiAssetList(
        items=assets,
        cursor=next_cursor,
        has_more=has_more,
    )


def get_dg_plus_api_asset_with_status_via_graphql(
    client: IGraphQLClient, asset_key_parts: list[str]
) -> DgApiAsset:
    """Single asset fetch with status information."""
    variables = {"assetKeys": [{"path": asset_key_parts}]}

    result = client.execute(ASSETS_WITH_STATUS_QUERY, variables=variables)

    # Handle assetsOrError response structure
    assets_or_error = result.get("assetsOrError", {})
    if assets_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {assets_or_error.get('message', 'Unknown error')}")

    asset_nodes = assets_or_error.get("nodes", [])

    # If an asset does not exist, it will return a node but the definition will be null
    node = asset_nodes[0]
    if node.get("definition") is None:
        raise Exception(f"Asset not found: {'/'.join(asset_key_parts)}")

    asset_key = "/".join(asset_key_parts)
    # Build metadata entries from definition
    definition_data = node.get("definition") or {}
    metadata_entries = []
    for entry in definition_data.get("metadataEntries", []):
        metadata_dict = {
            "label": entry.get("label", ""),
            "description": entry.get("description", ""),
        }

        for field in [
            "text",
            "url",
            "path",
            "jsonString",
            "mdStr",
            "floatValue",
            "intValue",
            "boolValue",
        ]:
            if field in entry:
                metadata_dict[field] = entry[field]
        if "module" in entry and "name" in entry:
            metadata_dict.update({"module": entry["module"], "name": entry["name"]})

        metadata_entries.append(metadata_dict)

    # Extract dependency keys
    dependency_keys = _extract_dependency_keys(definition_data.get("dependencyKeys", []))

    # Build status data
    status = _transform_asset_status_data(node)

    return DgApiAsset(
        id=node["id"],
        asset_key=asset_key,
        asset_key_parts=asset_key_parts,
        description=definition_data.get("description"),
        group_name=definition_data.get("groupName", ""),
        kinds=definition_data.get("kinds", []),
        metadata_entries=metadata_entries,
        dependency_keys=dependency_keys,
        status=status,
    )
