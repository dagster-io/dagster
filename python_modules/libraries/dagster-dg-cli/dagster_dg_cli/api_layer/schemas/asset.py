"""Asset models for REST-like API."""

from pydantic import BaseModel


class DgApiAssetHealthMetadata(BaseModel):
    """Asset health metadata details."""

    failed_run_id: str | None
    num_failed_partitions: int | None
    num_missing_partitions: int | None
    total_num_partitions: int | None
    num_failed_checks: int | None
    num_warning_checks: int | None
    total_num_checks: int | None
    last_materialized_timestamp: float | None


class DgApiAssetMaterialization(BaseModel):
    """Latest asset materialization information."""

    timestamp: float | None
    run_id: str | None
    partition: str | None


class DgApiAssetFreshnessInfo(BaseModel):
    """Asset freshness information."""

    current_lag_minutes: float | None
    current_minutes_late: float | None
    latest_materialization_minutes_late: float | None
    maximum_lag_minutes: float | None
    cron_schedule: str | None


class DgApiAssetChecksStatus(BaseModel):
    """Asset checks execution status."""

    status: str | None  # HEALTHY, WARNING, DEGRADED, UNKNOWN, NOT_APPLICABLE
    num_failed_checks: int | None
    num_warning_checks: int | None
    total_num_checks: int | None


class DgApiAssetStatus(BaseModel):
    """Asset status information for status view."""

    asset_health: str | None  # Overall health status
    materialization_status: str | None
    freshness_status: str | None
    asset_checks_status: str | None
    health_metadata: DgApiAssetHealthMetadata | None
    latest_materialization: DgApiAssetMaterialization | None
    freshness_info: DgApiAssetFreshnessInfo | None
    checks_status: DgApiAssetChecksStatus | None


class DgApiAsset(BaseModel):
    """Asset resource model."""

    id: str
    asset_key: str  # "my/asset/key"
    asset_key_parts: list[str]  # ["my", "asset", "key"]
    description: str | None
    group_name: str
    kinds: list[str]
    metadata_entries: list[dict]
    dependency_keys: list[str] = []  # ["dep/one", "dep/two"]
    # Status fields - populated only for status view
    status: DgApiAssetStatus | None = None

    class Config:
        from_attributes = True


class DgApiAssetList(BaseModel):
    """GET /api/assets response."""

    items: list[DgApiAsset]
    cursor: str | None  # Next cursor for pagination
    has_more: bool  # Whether more results exist
