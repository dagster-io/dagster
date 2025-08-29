"""GraphQL implementation for asset operations."""

from typing import Optional

from dagster_dg_cli.dagster_plus_api.schemas.asset import DgApiAsset, DgApiAssetList
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
