from typing import Any, ClassVar, Mapping, Optional, Sequence

from typing_extensions import Self

from ._io.base import ExternalExecutionContextLoader, ExternalExecutionMessageWriter
from ._io.default import ExternalExecutionFileContextLoader, ExternalExecutionFileMessageWriter
from ._protocol import (
    ExternalExecutionContextData,
    ExternalExecutionDataProvenance,
    ExternalExecutionMessage,
    ExternalExecutionPartitionKeyRange,
    ExternalExecutionTimeWindow,
)
from ._util import (
    assert_defined_asset_property,
    assert_defined_extra,
    assert_defined_partition_property,
    assert_param_json_serializable,
    assert_param_type,
    assert_param_value,
    assert_single_asset,
    emit_orchestration_inactive_warning,
    get_mock,
    is_dagster_orchestration_active,
)


def init_dagster_externals(
    *,
    context_loader: Optional[ExternalExecutionContextLoader] = None,
    message_writer: Optional[ExternalExecutionMessageWriter] = None,
) -> "ExternalExecutionContext":
    if ExternalExecutionContext.is_initialized():
        return ExternalExecutionContext.get()

    if is_dagster_orchestration_active():
        context_loader = context_loader or ExternalExecutionFileContextLoader()
        message_writer = message_writer or ExternalExecutionFileMessageWriter()
        data = context_loader.load_context()
        context = ExternalExecutionContext(data, message_writer)
    else:
        emit_orchestration_inactive_warning()
        context = get_mock()
    ExternalExecutionContext.set(context)
    return context


class ExternalExecutionContext:
    _instance: ClassVar[Optional[Self]] = None

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def set(cls, context: Self) -> None:
        cls._instance = context

    @classmethod
    def get(cls) -> Self:
        if cls._instance is None:
            raise Exception(
                "ExternalExecutionContext has not been initialized. You must call"
                " `init_dagster_externals()`."
            )
        return cls._instance

    def __init__(
        self, data: ExternalExecutionContextData, message_writer: ExternalExecutionMessageWriter
    ) -> None:
        self._data = data
        self.message_writer = message_writer

    def _send_message(self, method: str, params: Optional[Mapping[str, Any]] = None) -> None:
        message = ExternalExecutionMessage(method=method, params=params)
        self.message_writer.write_message(message)

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
    def provenance(self) -> Optional[ExternalExecutionDataProvenance]:
        provenance_by_asset_key = assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance"
        )
        assert_single_asset(self._data, "provenance")
        return list(provenance_by_asset_key.values())[0]

    @property
    def provenance_by_asset_key(self) -> Mapping[str, Optional[ExternalExecutionDataProvenance]]:
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
    def partition_key_range(self) -> Optional["ExternalExecutionPartitionKeyRange"]:
        partition_key_range = assert_defined_partition_property(
            self._data["partition_key_range"], "partition_key_range"
        )
        return partition_key_range

    @property
    def partition_time_window(self) -> Optional["ExternalExecutionTimeWindow"]:
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
    def job_name(self) -> Optional[str]:
        return self._data["job_name"]

    @property
    def retry_number(self) -> int:
        return self._data["retry_number"]

    def get_extra(self, key: str) -> Any:
        return assert_defined_extra(self._data["extras"], key)

    @property
    def extras(self) -> Mapping[str, Any]:
        return self._data["extras"]

    # ##### WRITE

    def report_asset_metadata(self, asset_key: str, label: str, value: Any) -> None:
        asset_key = assert_param_type(asset_key, str, "report_asset_metadata", "asset_key")
        label = assert_param_type(label, str, "report_asset_metadata", "label")
        value = assert_param_json_serializable(value, "report_asset_metadata", "value")
        self._send_message(
            "report_asset_metadata", {"asset_key": asset_key, "label": label, "value": value}
        )

    def report_asset_data_version(self, asset_key: str, data_version: str) -> None:
        asset_key = assert_param_type(asset_key, str, "report_asset_data_version", "asset_key")
        data_version = assert_param_type(
            data_version, str, "report_asset_data_version", "data_version"
        )
        self._send_message(
            "report_asset_data_version", {"asset_key": asset_key, "data_version": data_version}
        )

    def log(self, message: str, level: str = "info") -> None:
        message = assert_param_type(message, str, "log", "asset_key")
        level = assert_param_value(level, ["info", "warning", "error"], "log", "level")
        self._send_message("log", {"message": message, "level": level})
