from typing import Any, Mapping, Optional, Sequence

from typing_extensions import Final, TypeAlias, TypedDict

ExternalExecutionExtras: TypeAlias = Mapping[str, Any]

ENV_KEY_PREFIX: Final = "DAGSTER_EXTERNALS_"


def _param_name_to_env_key(key: str) -> str:
    return f"{ENV_KEY_PREFIX}{key.upper()}"


# ##### PARAMETERS

DAGSTER_EXTERNALS_ENV_KEYS: Final = {
    k: _param_name_to_env_key(k) for k in ("is_orchestration_active", "context", "messages")
}


# ##### MESSAGE


class ExternalExecutionMessage(TypedDict):
    method: str
    params: Optional[Mapping[str, Any]]


# ##### EXTERNAL EXECUTION CONTEXT


class ExternalExecutionContextData(TypedDict):
    asset_keys: Optional[Sequence[str]]
    code_version_by_asset_key: Optional[Mapping[str, Optional[str]]]
    provenance_by_asset_key: Optional[Mapping[str, Optional["ExternalExecutionDataProvenance"]]]
    partition_key: Optional[str]
    partition_key_range: Optional["ExternalExecutionPartitionKeyRange"]
    partition_time_window: Optional["ExternalExecutionTimeWindow"]
    run_id: str
    job_name: Optional[str]
    retry_number: int
    extras: Mapping[str, Any]


class ExternalExecutionPartitionKeyRange(TypedDict):
    start: str
    end: str


class ExternalExecutionTimeWindow(TypedDict):
    start: str  # timestamp
    end: str  # timestamp


class ExternalExecutionDataProvenance(TypedDict):
    code_version: str
    input_data_versions: Mapping[str, str]
    is_user_provided: bool
