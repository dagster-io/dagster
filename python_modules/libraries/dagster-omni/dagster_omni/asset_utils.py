from collections.abc import Iterator
from typing import Any, Optional, Union

from dagster import AssetObservation, AssetSpec, Output
from dagster._time import get_current_timestamp

from dagster_omni.translator import OmniContentType, OmniMetadataSet, OmniTagSet


def create_omni_asset_observation(
    content_data: dict[str, Any],
    spec: AssetSpec,
) -> Iterator[AssetObservation]:
    """Create an asset observation for Omni content."""
    metadata = {}

    # Add basic metadata from the content
    if "name" in content_data:
        metadata["omni_name"] = content_data["name"]
    if "createdAt" in content_data:
        metadata["created_at"] = content_data["createdAt"]
    if "updatedAt" in content_data:
        metadata["updated_at"] = content_data["updatedAt"]
    if "id" in content_data:
        metadata["omni_id"] = content_data["id"]

    # Add content-type specific metadata
    content_type = content_data.get("type", "unknown")

    if content_type == "model":
        # Add model-specific metadata
        if "connectionId" in content_data:
            metadata["connection_id"] = content_data["connectionId"]
        if "modelKind" in content_data:
            metadata["model_kind"] = content_data["modelKind"]
    elif content_type == "workbook":
        # Add workbook-specific metadata
        if "owner" in content_data:
            metadata["owner"] = content_data["owner"]
    elif content_type == "query":
        # Add query-specific metadata
        if "sql" in content_data:
            metadata["query_sql"] = content_data["sql"][:500]  # Truncate long SQL

    yield AssetObservation(
        asset_key=spec.key,
        metadata=metadata,
    )


def create_omni_asset_materialization(
    content_data: dict[str, Any],
    spec: AssetSpec,
    execution_result: Optional[dict[str, Any]] = None,
) -> Iterator[Union[Output, AssetObservation]]:
    """Create an asset materialization for Omni content with optional execution results."""
    omni_tags = OmniTagSet.extract(spec.tags)
    asset_type = omni_tags.asset_type

    metadata = {}

    # Add execution results if available (for queries)
    if execution_result and asset_type == OmniContentType.QUERY.value:
        metadata["execution_status"] = execution_result.get("status", "unknown")
        metadata["execution_time"] = execution_result.get("executionTime", 0)
        metadata["row_count"] = execution_result.get("rowCount", 0)

        # Add query performance metrics if available
        if "statistics" in execution_result:
            stats = execution_result["statistics"]
            metadata["bytes_processed"] = stats.get("bytesProcessed", 0)
            metadata["cache_hit"] = stats.get("cacheHit", False)

    # Add standard metadata from content
    if "name" in content_data:
        metadata["omni_name"] = content_data["name"]
    if "updatedAt" in content_data:
        metadata["last_updated"] = content_data["updatedAt"]

    metadata["materialized_at"] = get_current_timestamp()

    yield Output(
        value=content_data,
        metadata=metadata,
    )


def get_omni_url_for_asset(spec: AssetSpec) -> str:
    """Generate the Omni web UI URL for an asset."""
    omni_metadata = OmniMetadataSet.extract(spec.metadata)
    omni_tags = OmniTagSet.extract(spec.tags)

    workspace_url = omni_metadata.workspace_url.rstrip("/")
    asset_id = omni_metadata.id
    asset_type = omni_tags.asset_type

    # Generate URLs based on asset type
    # Note: These URL patterns are estimates and may need adjustment based on actual Omni UI
    if asset_type == OmniContentType.MODEL.value:
        return f"{workspace_url}/models/{asset_id}"
    elif asset_type == OmniContentType.WORKBOOK.value:
        return f"{workspace_url}/workbooks/{asset_id}"
    elif asset_type == OmniContentType.QUERY.value:
        return f"{workspace_url}/queries/{asset_id}"
    else:
        return workspace_url
