"""Asset models for REST-like API."""

from typing import Literal

from pydantic import BaseModel

DgApiEventType = Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"]


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

    asset_key: str  # Slash-separated asset key (e.g., "my/asset/key")
    asset_health: str | None  # Overall health status
    materialization_status: str | None
    freshness_status: str | None
    asset_checks_status: str | None
    health_metadata: DgApiAssetHealthMetadata | None
    latest_materialization: DgApiAssetMaterialization | None
    freshness_info: DgApiAssetFreshnessInfo | None
    checks_status: DgApiAssetChecksStatus | None


class DgApiAutomationCondition(BaseModel):
    """Automation condition attached to an asset."""

    label: str | None
    expanded_label: list[str]


class DgApiPartitionDefinition(BaseModel):
    """Partition definition for an asset."""

    description: str


class DgApiPartitionMapping(BaseModel):
    """Mapping of partitions between an asset and a dependency."""

    class_name: str
    description: str


class DgApiAssetDependency(BaseModel):
    """An upstream dependency with optional partition mapping."""

    asset_key: str
    partition_mapping: DgApiPartitionMapping | None


class DgApiBackfillPolicy(BaseModel):
    """Backfill policy for a partitioned asset."""

    max_partitions_per_run: int | None


class DgAssetBase(BaseModel):
    """Common asset fields shared by API and local list models."""

    asset_key: str  # "my/asset/key"
    asset_key_parts: list[str]  # ["my", "asset", "key"]
    description: str | None = None
    group_name: str | None = None
    kinds: list[str] = []
    dependency_keys: list[str] = []  # ["dep/one", "dep/two"]
    owners: list[dict] | None = None
    tags: list[dict] | None = None  # [{key: str, value: str}]
    automation_condition: DgApiAutomationCondition | None = None


class DgApiAsset(DgAssetBase):
    """Asset resource model."""

    id: str
    metadata_entries: list[dict]
    # Extended detail fields - populated only for get (single asset)
    partition_definition: DgApiPartitionDefinition | None = None
    backfill_policy: DgApiBackfillPolicy | None = None
    job_names: list[str] | None = None
    upstream_dependencies: list[DgApiAssetDependency] | None = None
    downstream_keys: list[str] | None = None

    class Config:
        from_attributes = True


class DgApiAssetList(BaseModel):
    """GET /api/assets response."""

    items: list[DgApiAsset]
    cursor: str | None  # Next cursor for pagination
    has_more: bool  # Whether more results exist


class DgApiAssetEvent(BaseModel):
    """A materialization or observation event for an asset."""

    timestamp: str  # millisecond timestamp string from GraphQL
    run_id: str
    event_type: Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"]
    partition: str | None
    tags: list[dict]
    metadata_entries: list[dict]


class DgApiAssetEventList(BaseModel):
    """GET /api/assets/{key}/events response."""

    items: list[DgApiAssetEvent]


class DgApiEvaluationNode(BaseModel):
    """A node in the automation condition evaluation tree."""

    unique_id: str
    user_label: str | None
    expanded_label: list[str]
    start_timestamp: float | None
    end_timestamp: float | None
    num_true: int | None
    num_candidates: int | None
    is_partitioned: bool
    child_unique_ids: list[str]
    operator_type: str


class DgApiEvaluationRecord(BaseModel):
    """An automation condition evaluation record for an asset."""

    evaluation_id: int
    timestamp: float
    num_requested: int | None
    run_ids: list[str]
    start_timestamp: float | None
    end_timestamp: float | None
    root_unique_id: str
    evaluation_nodes: list[DgApiEvaluationNode] | None = None


class DgApiEvaluationRecordList(BaseModel):
    """GET /api/assets/{key}/evaluations response."""

    items: list[DgApiEvaluationRecord]


class DgApiPartitionStats(BaseModel):
    """Partition materialization statistics for an asset."""

    num_materialized: int
    num_failed: int
    num_materializing: int
    num_partitions: int
