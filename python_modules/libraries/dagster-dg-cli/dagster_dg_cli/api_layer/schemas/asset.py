"""Asset models for REST-like API."""

from typing import Optional

from pydantic import BaseModel


class DgApiAssetHealthMetadata(BaseModel):
    """Asset health metadata details."""

    failed_run_id: Optional[str]
    num_failed_partitions: Optional[int]
    num_missing_partitions: Optional[int]
    total_num_partitions: Optional[int]
    num_failed_checks: Optional[int]
    num_warning_checks: Optional[int]
    total_num_checks: Optional[int]
    last_materialized_timestamp: Optional[float]


class DgApiAssetMaterialization(BaseModel):
    """Latest asset materialization information."""

    timestamp: Optional[float]
    run_id: Optional[str]
    partition: Optional[str]


class DgApiAssetFreshnessInfo(BaseModel):
    """Asset freshness information."""

    current_lag_minutes: Optional[float]
    current_minutes_late: Optional[float]
    latest_materialization_minutes_late: Optional[float]
    maximum_lag_minutes: Optional[float]
    cron_schedule: Optional[str]


class DgApiAssetChecksStatus(BaseModel):
    """Asset checks execution status."""

    status: Optional[str]  # HEALTHY, WARNING, DEGRADED, UNKNOWN, NOT_APPLICABLE
    num_failed_checks: Optional[int]
    num_warning_checks: Optional[int]
    total_num_checks: Optional[int]


class DgApiAssetStatus(BaseModel):
    """Asset status information for status view."""

    asset_health: Optional[str]  # Overall health status
    materialization_status: Optional[str]
    freshness_status: Optional[str]
    asset_checks_status: Optional[str]
    health_metadata: Optional[DgApiAssetHealthMetadata]
    latest_materialization: Optional[DgApiAssetMaterialization]
    freshness_info: Optional[DgApiAssetFreshnessInfo]
    checks_status: Optional[DgApiAssetChecksStatus]


class DgApiAsset(BaseModel):
    """Asset resource model."""

    id: str
    asset_key: str  # "my/asset/key"
    asset_key_parts: list[str]  # ["my", "asset", "key"]
    description: Optional[str]
    group_name: str
    kinds: list[str]
    metadata_entries: list[dict]
    dependency_keys: list[str] = []  # ["dep/one", "dep/two"]
    # Status fields - populated only for status view
    status: Optional[DgApiAssetStatus] = None

    class Config:
        from_attributes = True


class DgApiAssetList(BaseModel):
    """GET /api/assets response."""

    items: list[DgApiAsset]
    cursor: Optional[str]  # Next cursor for pagination
    has_more: bool  # Whether more results exist
