import json
import sys
from typing import IO, Any, ClassVar, Mapping, Optional, Sequence

from typing_extensions import Self

from dagster_external.params import get_external_execution_params

from .protocol import (
    ExternalDataProvenance,
    ExternalExecutionContextData,
    ExternalExecutionIOMode,
    ExternalPartitionKeyRange,
    ExternalTimeWindow,
    Notification,
)
from .util import (
    assert_defined_asset_property,
    assert_defined_extra,
    assert_defined_partition_property,
    assert_param_json_serializable,
    assert_param_type,
    assert_param_value,
    assert_single_asset,
)


def init_dagster_external() -> "ExternalExecutionContext":
    params = get_external_execution_params()
    if params.input_mode == ExternalExecutionIOMode.stdio:
        input_stream = sys.stdin
    elif params.input_mode == ExternalExecutionIOMode.file:
        assert params.input_path, "input_path must be set when input_mode is `file`"
        input_stream = open(params.input_path, "r")
    elif params.input_mode == ExternalExecutionIOMode.fifo:
        assert params.input_path, "input_path must be set when input_mode is `fifo`"
        input_stream = open(params.input_path, "r")
    else:
        raise Exception(f"Invalid input mode: {params.input_mode}")

    if params.output_mode == ExternalExecutionIOMode.stdio:
        output_stream = sys.stdout
    elif params.output_mode == ExternalExecutionIOMode.file:
        assert params.output_path, "output_path must be set when output_mode is `file`"
        output_stream = open(params.output_path, "a")
    elif params.output_mode == ExternalExecutionIOMode.fifo:
        assert params.output_path, "output_path must be set when output_mode is `fifo`"
        output_stream = open(params.output_path, "w")
    else:
        raise Exception(f"Invalid output mode: {params.output_mode}")
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
    def is_asset_step(self) -> bool:
        return self._data["asset_keys"] is not None

    @property
    def asset_key(self) -> str:
        asset_keys = assert_defined_asset_property(self._data["asset_keys"], "asset_key")
        assert_single_asset(self._data, "asset_key")
        return asset_keys[0]

    @property
    def asset_keys(self) -> Sequence[str]:
        asset_keys = assert_defined_asset_property(self._data["asset_keys"], "asset_keys")
        return asset_keys

    @property
    def provenance(self) -> Optional[ExternalDataProvenance]:
        provenance_by_asset_key = assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance"
        )
        assert_single_asset(self._data, "provenance")
        return list(provenance_by_asset_key.values())[0]

    @property
    def provenance_by_asset_key(self) -> Mapping[str, Optional[ExternalDataProvenance]]:
        provenance_by_asset_key = assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance_by_asset_key"
        )
        return provenance_by_asset_key

    @property
    def code_version(self) -> Optional[str]:
        code_version_by_asset_key = assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version"
        )
        assert_single_asset(self._data, "code_version")
        return list(code_version_by_asset_key.values())[0]

    @property
    def code_version_by_asset_key(self) -> Mapping[str, Optional[str]]:
        code_version_by_asset_key = assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version_by_asset_key"
        )
        return code_version_by_asset_key

    @property
    def is_partition_step(self) -> bool:
        return self._data["partition_key_range"] is not None

    @property
    def partition_key(self) -> str:
        partition_key = assert_defined_partition_property(
            self._data["partition_key"], "partition_key"
        )
        return partition_key

    @property
    def partition_key_range(self) -> Optional["ExternalPartitionKeyRange"]:
        partition_key_range = assert_defined_partition_property(
            self._data["partition_key_range"], "partition_key_range"
        )
        return partition_key_range

    @property
    def partition_time_window(self) -> Optional["ExternalTimeWindow"]:
        # None is a valid value for partition_time_window, but we check that a partition key range
        # is defined.
        assert_defined_partition_property(
            self._data["partition_key_range"], "partition_time_window"
        )
        return self._data["partition_time_window"]

    @property
    def run_id(self) -> str:
        return self._data["run_id"]

    @property
    def job_name(self) -> str:
        return self._data["job_name"]

    @property
    def retry_number(self) -> int:
        return self._data["retry_number"]

    def get_extra(self, key: str) -> Any:
        return assert_defined_extra(self._data["extras"], key)

    # ##### WRITE

    def report_asset_metadata(self, asset_key: str, label: str, value: Any) -> None:
        asset_key = assert_param_type(asset_key, str, "report_asset_metadata", "asset_key")
        label = assert_param_type(label, str, "report_asset_metadata", "label")
        value = assert_param_json_serializable(value, "report_asset_metadata", "value")
        self._send_notification(
            "report_asset_metadata", {"asset_key": asset_key, "label": label, "value": value}
        )

    def report_asset_data_version(self, asset_key: str, data_version: str) -> None:
        asset_key = assert_param_type(asset_key, str, "report_asset_data_version", "asset_key")
        data_version = assert_param_type(
            data_version, str, "report_asset_data_version", "data_version"
        )
        self._send_notification(
            "report_asset_data_version", {"asset_key": asset_key, "data_version": data_version}
        )

    def log(self, message: str, level: str = "info") -> None:
        message = assert_param_type(message, str, "log", "asset_key")
        level = assert_param_value(level, ["info", "warning", "error"], "log", "level")
        self._send_notification("log", {"message": message, "level": level})
