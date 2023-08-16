from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from typing_extensions import Final, TypeAlias, TypedDict

ExternalExecutionExtras: TypeAlias = Mapping[str, Any]

# ##### PARAMETERS

DAGSTER_EXTERNAL_DEFAULT_HOST: Final = "localhost"
DAGSTER_EXTERNAL_DEFAULT_PORT: Final = 9716
DAGSTER_EXTERNAL_DEFAULT_INPUT_MODE: Final = "stdio"
DAGSTER_EXTERNAL_DEFAULT_OUTPUT_MODE: Final = "stdio"
DAGSTER_EXTERNAL_DEFAULT_INPUT_FILENAME: Final = "dagster_external_input"
DAGSTER_EXTERNAL_DEFAULT_OUTPUT_FILENAME: Final = "dagster_external_output"

DAGSTER_EXTERNAL_ENV_KEYS: Final = {
    "input_mode": "DAGSTER_EXTERNAL_INPUT_MODE",
    "output_mode": "DAGSTER_EXTERNAL_OUTPUT_MODE",
    "input": "DAGSTER_EXTERNAL_INPUT",
    "output": "DAGSTER_EXTERNAL_OUTPUT",
    "host": "DAGSTER_EXTERNAL_HOST",
    "port": "DAGSTER_EXTERNAL_PORT",
}

# ##### SOCKET SERVER


class SocketServerControlMessage(str, Enum):
    shutdown = "__shutdown__"
    get_context = "__get_context__"
    initiate_client_stream = "__initiate_client_stream__"


# ##### IO MODES


class ExternalExecutionIOMode(str, Enum):
    stdio = "stdio"
    file = "file"
    fifo = "fifo"
    socket = "socket"


# ##### NOTIFICATION


class Notification(TypedDict):
    method: str
    params: Optional[Mapping[str, Any]]


# ##### EXTERNAL EXECUTION CONTEXT


class ExternalExecutionContextData(TypedDict):
    asset_keys: Optional[Sequence[str]]
    code_version_by_asset_key: Optional[Mapping[str, Optional[str]]]
    provenance_by_asset_key: Optional[Mapping[str, Optional["ExternalDataProvenance"]]]
    partition_key: Optional[str]
    partition_key_range: Optional["ExternalPartitionKeyRange"]
    partition_time_window: Optional["ExternalTimeWindow"]
    run_id: str
    job_name: str
    retry_number: int
    extras: Mapping[str, Any]


class ExternalPartitionKeyRange(TypedDict):
    start: str
    end: str


class ExternalTimeWindow(TypedDict):
    start: str  # timestamp
    end: str  # timestamp


class ExternalDataProvenance(TypedDict):
    code_version: str
    input_data_versions: Mapping[str, str]
    is_user_provided: bool
