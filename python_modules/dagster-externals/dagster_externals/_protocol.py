from typing import Any, Mapping, Optional, Sequence, TypedDict

ExtExtras = Mapping[str, Any]
ExtParams = Mapping[str, Any]


ENV_KEY_PREFIX = "DAGSTER_EXTERNALS_"


def _param_name_to_env_key(key: str) -> str:
    return f"{ENV_KEY_PREFIX}{key.upper()}"


# ##### PARAMETERS

DAGSTER_EXTERNALS_ENV_KEYS = {
    k: _param_name_to_env_key(k) for k in ("launched_by_ext_client", "context", "messages")
}


# ##### MESSAGE


class ExtMessage(TypedDict):
    method: str
    params: Optional[Mapping[str, Any]]


# ##### EXTERNAL EXECUTION CONTEXT


class ExtContextData(TypedDict):
    asset_keys: Optional[Sequence[str]]
    code_version_by_asset_key: Optional[Mapping[str, Optional[str]]]
    provenance_by_asset_key: Optional[Mapping[str, Optional["ExtDataProvenance"]]]
    partition_key: Optional[str]
    partition_key_range: Optional["ExtPartitionKeyRange"]
    partition_time_window: Optional["ExtTimeWindow"]
    run_id: str
    job_name: Optional[str]
    retry_number: int
    extras: Mapping[str, Any]


class ExtPartitionKeyRange(TypedDict):
    start: str
    end: str


class ExtTimeWindow(TypedDict):
    start: str  # timestamp
    end: str  # timestamp


class ExtDataProvenance(TypedDict):
    code_version: str
    input_data_versions: Mapping[str, str]
    is_user_provided: bool
