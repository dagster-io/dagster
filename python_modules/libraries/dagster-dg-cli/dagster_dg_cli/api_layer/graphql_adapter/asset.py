"""GraphQL implementation for asset operations."""

from typing import Optional

from dagster_dg_cli.api_layer.schemas.asset import (
    DgApiAsset,
    DgApiAssetFreshnessInfo,
    DgApiAssetList,
    DgApiAssetMaterialization,
    DgApiAssetStatus,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

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

        asset = DgApiAsset(
            id=node["id"],
            asset_key=asset_key,
            asset_key_parts=asset_key_parts,
            description=node.get("description"),
            group_name=node.get("groupName", ""),
            kinds=node.get("kinds", []),
            metadata_entries=metadata_entries,
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

    return DgApiAsset(
        id=node["id"],
        asset_key=asset_key,
        asset_key_parts=asset_key_parts,
        description=node.get("description"),
        group_name=node.get("groupName", ""),
        kinds=node.get("kinds", []),
        metadata_entries=metadata_entries,
    )


# Status view GraphQL queries - using only assetNodes (no assets field available)
ASSETS_WITH_STATUS_QUERY = """
query AssetsWithStatus($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
        id
        assetKey { path }
        description
        groupName
        kinds
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
        # Freshness information
        freshnessInfo {
            currentLagMinutes
            currentMinutesLate
            latestMaterializationMinutesLate
        }
        freshnessPolicy {
            maximumLagMinutes
            cronSchedule
        }
        # Latest materialization with partition info
        latestMaterializationByPartition(partitions: []) {
            timestamp
            runId
            partition
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


def _transform_asset_status_data(asset_node_data) -> DgApiAssetStatus:
    """Transform GraphQL node data into status format."""
    # Note: Asset health data is not available in the current Dagster Plus API
    # This is a simplified status view with available data

    # Extract freshness info
    freshness_info = None
    if asset_node_data:
        freshness_data = asset_node_data.get("freshnessInfo", {})
        freshness_policy = asset_node_data.get("freshnessPolicy", {})

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

    # Extract latest materialization
    latest_materialization = None
    if asset_node_data:
        mat_events = asset_node_data.get("latestMaterializationByPartition", [])
        if mat_events:
            latest = mat_events[0]  # Take most recent
            latest_materialization = DgApiAssetMaterialization(
                timestamp=latest.get("timestamp"),
                run_id=latest.get("runId"),
                partition=latest.get("partition"),
            )

    # Return status with available data (no health data available in current API)
    return DgApiAssetStatus(
        asset_health=None,
        materialization_status=None,
        freshness_status=None,
        asset_checks_status=None,
        health_metadata=None,
        latest_materialization=latest_materialization,
        freshness_info=freshness_info,
        checks_status=None,
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
    asset_nodes = status_result.get("assetNodes", [])

    # Step 3: Transform and combine data
    assets = []

    # Create lookup map for efficient merging
    nodes_by_key = {"/".join(node["assetKey"]["path"]): node for node in asset_nodes}

    for record in records:
        asset_key_parts = record["key"]["path"]
        asset_key = "/".join(asset_key_parts)

        # Get corresponding node data
        node_data = nodes_by_key.get(asset_key)

        if not node_data:
            continue  # Skip if we don't have node data

        # Build basic asset data
        metadata_entries = []
        for entry in node_data.get("metadataEntries", []):
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

        # Build status data
        status = _transform_asset_status_data(node_data)

        asset = DgApiAsset(
            id=node_data["id"],
            asset_key=asset_key,
            asset_key_parts=asset_key_parts,
            description=node_data.get("description"),
            group_name=node_data.get("groupName", ""),
            kinds=node_data.get("kinds", []),
            metadata_entries=metadata_entries,
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
    asset_nodes = result.get("assetNodes", [])

    if not asset_nodes:
        raise Exception(f"Asset not found: {'/'.join(asset_key_parts)}")

    node = asset_nodes[0]
    asset_key = "/".join(asset_key_parts)

    # Build metadata entries (same logic as existing)
    metadata_entries = []
    for entry in node.get("metadataEntries", []):
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

    # Build status data
    status = _transform_asset_status_data(node)

    return DgApiAsset(
        id=node["id"],
        asset_key=asset_key,
        asset_key_parts=asset_key_parts,
        description=node.get("description"),
        group_name=node.get("groupName", ""),
        kinds=node.get("kinds", []),
        metadata_entries=metadata_entries,
        status=status,
    )
