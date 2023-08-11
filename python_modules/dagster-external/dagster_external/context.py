import json
import os
import sys
from typing import IO, Any, ClassVar, Mapping, Optional

from typing_extensions import Self

from .protocol import (
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalDataProvenance,
    ExternalExecutionContextData,
    ExternalPartitionKeyRange,
    ExternalTimeWindow,
    Notification,
)


def init_dagster_external() -> "ExternalExecutionContext":
    input_mode = os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["input_mode"], "stdin")
    if input_mode == "stdio":
        input_stream = sys.stdin
    elif input_mode == "fifo":
        fifo_path = os.environ[DAGSTER_EXTERNAL_ENV_KEYS["input"]]
        input_stream = open(fifo_path, "r")
    else:
        raise Exception(f"Invalid input mode: {input_mode}")

    output_mode = os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["output_mode"], "stdout")
    if output_mode == "stdio":
        output_stream = sys.stdout
    elif output_mode == "fifo":
        fifo_path = os.environ[DAGSTER_EXTERNAL_ENV_KEYS["output"]]
        output_stream = open(fifo_path, "w")
    else:
        raise Exception(f"Invalid output mode: {output_mode}")

    with input_stream as f:
        data = json.load(f)
    context = ExternalExecutionContext(data, output_stream)
    ExternalExecutionContext.set(context)
    return context


class ExternalExecutionContext:
    _instance: ClassVar[Optional[Self]] = None

    @classmethod
    def set(cls, context: Self) -> None:
        cls._instance = context

    @classmethod
    def get(cls) -> Self:
        if cls._instance is None:
            raise Exception(
                "ExternalExecutionContext has not been initialized. You must call"
                " `init_dagster_external()`."
            )
        return cls._instance

    def __init__(self, data: ExternalExecutionContextData, output_stream: IO) -> None:
        self._data = data
        self._output_stream = output_stream

    def _send_notification(self, method: str, params: Optional[Mapping[str, Any]] = None) -> None:
        notification = Notification(method=method, params=params)
        self._output_stream.write(json.dumps(notification) + "\n")

    # ########################
    # ##### PUBLIC API
    # ########################

    @property
    def asset_key(self) -> str:
        return self._data["asset_key"]

    @property
    def code_version(self) -> Optional[str]:
        return self._data["code_version"]

    @property
    def data_provenance(self) -> Optional["ExternalDataProvenance"]:
        return self._data["data_provenance"]

    @property
    def partition_key(self) -> Optional[str]:
        return self._data["partition_key"]

    @property
    def partition_key_range(self) -> Optional["ExternalPartitionKeyRange"]:
        return self._data["partition_key_range"]

    @property
    def partition_time_window(self) -> Optional["ExternalTimeWindow"]:
        return self._data["partition_time_window"]

    @property
    def run_id(self) -> str:
        return self._data["run_id"]

    @property
    def tags(self) -> Mapping[str, str]:
        return self._data["run_tags"]

    @property
    def userdata(self) -> Mapping[str, Any]:
        return self._data["userdata"]

    def report_asset_metadata(self, label: str, value: Any) -> None:
        assert isinstance(label, str)
        self._send_notification("report_asset_metadata", {"label": label, "value": value})

    def report_asset_data_version(self, value: Any) -> None:
        assert isinstance(value, str)
        self._send_notification("report_asset_data_version", {"value": value})

    def log(self, message: str, level: str = "info") -> None:
        assert isinstance(message, str)
        assert level in ["info", "warning", "error"]
        self._send_notification("log", {"message": message, "level": level})
