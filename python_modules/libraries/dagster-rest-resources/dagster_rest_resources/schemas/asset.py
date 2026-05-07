from typing import Literal

from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiAssetHealthStatus
from dagster_rest_resources.schemas.util import DgApiList, DgApiPaginatedList

DgApiEventType = Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"]


class DgApiAssetHealthMetadata(BaseModel):
    failed_run_id: str | None
    num_failed_partitions: int | None
    num_missing_partitions: int | None
    total_num_partitions: int | None
    num_failed_checks: int | None
    num_warning_checks: int | None
    total_num_checks: int | None
    last_materialized_timestamp: float | None


class DgApiAssetMaterialization(BaseModel):
    timestamp: float | None
    run_id: str | None
    partition: str | None


class DgApiAssetFreshnessInfo(BaseModel):
    current_lag_minutes: float | None
    current_minutes_late: float | None
    latest_materialization_minutes_late: float | None
    maximum_lag_minutes: float | None
    cron_schedule: str | None


class DgApiAssetChecksStatus(BaseModel):
    status: DgApiAssetHealthStatus | None
    num_failed_checks: int | None
    num_warning_checks: int | None
    total_num_checks: int | None


class DgApiAssetStatus(BaseModel):
    asset_key: str  # Slash-separated asset key (e.g., "my/asset/key")
    asset_health: DgApiAssetHealthStatus | None  # Overall health status
    materialization_status: DgApiAssetHealthStatus | None
    freshness_status: DgApiAssetHealthStatus | None
    asset_checks_status: DgApiAssetHealthStatus | None
    health_metadata: DgApiAssetHealthMetadata | None
    latest_materialization: DgApiAssetMaterialization | None
    freshness_info: DgApiAssetFreshnessInfo | None
    checks_status: DgApiAssetChecksStatus | None


class DgApiAutomationCondition(BaseModel):
    label: str | None
    expanded_label: list[str]


class DgApiPartitionDefinition(BaseModel):
    description: str


class DgApiPartitionMapping(BaseModel):
    class_name: str
    description: str


class DgApiAssetDependency(BaseModel):
    asset_key: str
    partition_mapping: DgApiPartitionMapping | None


class DgApiBackfillPolicy(BaseModel):
    max_partitions_per_run: int | None


class DgApiAssetBase(BaseModel):
    asset_key: str  # "my/asset/key"
    asset_key_parts: list[str]  # ["my", "asset", "key"]
    description: str | None = None
    group_name: str | None = None
    kinds: list[str] = []
    dependency_keys: list[str] = []  # ["dep/one", "dep/two"]
    owners: list[dict] | None = None
    tags: list[dict] | None = None  # [{key: str, value: str}]
    automation_condition: DgApiAutomationCondition | None = None


class DgApiAsset(DgApiAssetBase):
    id: str
    metadata_entries: list[dict]
    # Extended detail fields - populated only for get (single asset)
    partition_definition: DgApiPartitionDefinition | None = None
    backfill_policy: DgApiBackfillPolicy | None = None
    job_names: list[str] | None = None
    upstream_dependencies: list[DgApiAssetDependency] | None = None
    downstream_keys: list[str] | None = None


class DgApiAssetList(DgApiPaginatedList[DgApiAsset]):
    pass


class DgApiAssetEvent(BaseModel):
    timestamp: str  # millisecond timestamp string from GraphQL
    run_id: str
    event_type: Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"]
    partition: str | None
    tags: list[dict]
    metadata_entries: list[dict]


class DgApiAssetEventList(DgApiList[DgApiAssetEvent]):
    pass


class DgApiEvaluationNode(BaseModel):
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
    evaluation_id: int
    timestamp: float
    num_requested: int | None
    run_ids: list[str]
    start_timestamp: float | None
    end_timestamp: float | None
    root_unique_id: str
    evaluation_nodes: list[DgApiEvaluationNode] | None = None


class DgApiEvaluationRecordList(DgApiList[DgApiEvaluationRecord]):
    pass


class DgApiPartitionStats(BaseModel):
    num_materialized: int
    num_failed: int
    num_materializing: int
    num_partitions: int
