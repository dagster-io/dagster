from dataclasses import dataclass
from typing import Any, Mapping, Optional

from dagster_ext import (
    DAGSTER_EXT_ENV_KEYS,
    EXT_METADATA_TYPE_INFER,
    IS_DAGSTER_EXT_PROCESS_ENV_VAR,
    ExtContextData,
    ExtDataProvenance,
    ExtExtras,
    ExtMessage,
    ExtMetadataType,
    ExtParams,
    ExtTimeWindow,
    encode_env_var,
)

import dagster._check as check
from dagster._core.definitions.data_version import DataProvenance, DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue, normalize_metadata_value
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.invocation import BoundOpExecutionContext


class ExtMessageHandler:
    def __init__(self, context: OpExecutionContext) -> None:
        self._context = context

    def _resolve_metadata_value(self, value: Any, metadata_type: ExtMetadataType) -> MetadataValue:
        if metadata_type == EXT_METADATA_TYPE_INFER:
            return normalize_metadata_value(value)
        elif metadata_type == "text":
            return MetadataValue.text(value)
        elif metadata_type == "url":
            return MetadataValue.url(value)
        elif metadata_type == "path":
            return MetadataValue.path(value)
        elif metadata_type == "notebook":
            return MetadataValue.notebook(value)
        elif metadata_type == "json":
            return MetadataValue.json(value)
        elif metadata_type == "md":
            return MetadataValue.md(value)
        elif metadata_type == "float":
            return MetadataValue.float(value)
        elif metadata_type == "int":
            return MetadataValue.int(value)
        elif metadata_type == "bool":
            return MetadataValue.bool(value)
        elif metadata_type == "dagster_run":
            return MetadataValue.dagster_run(value)
        elif metadata_type == "asset":
            return MetadataValue.asset(AssetKey.from_user_string(value))
        elif metadata_type == "table":
            return MetadataValue.table(value)
        elif metadata_type == "null":
            return MetadataValue.null()
        else:
            check.failed(f"Unexpected metadata type {metadata_type}")

    # Type ignores because we currently validate in individual handlers
    def handle_message(self, message: ExtMessage) -> None:
        if message["method"] == "report_asset_materialization":
            self._handle_report_asset_materialization(**message["params"])  # type: ignore
        elif message["method"] == "log":
            self._handle_log(**message["params"])  # type: ignore

    def _handle_report_asset_materialization(
        self, asset_key: str, metadata: Optional[Mapping[str, Any]], data_version: Optional[str]
    ) -> None:
        check.str_param(asset_key, "asset_key")
        check.opt_str_param(data_version, "data_version")
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        resolved_asset_key = AssetKey.from_user_string(asset_key)
        resolved_metadata = {
            k: self._resolve_metadata_value(v["raw_value"], v["type"]) for k, v in metadata.items()
        }
        if data_version is not None:
            self._context.set_data_version(resolved_asset_key, DataVersion(data_version))
        if resolved_metadata:
            output_name = self._context.output_for_asset_key(resolved_asset_key)
            self._context.add_output_metadata(resolved_metadata, output_name)

    def _handle_log(self, message: str, level: str = "info") -> None:
        check.str_param(message, "message")
        self._context.log.log(level, message)


def _ext_params_as_env_vars(
    context_injector_params: ExtParams, message_reader_params: ExtParams
) -> Mapping[str, str]:
    return {
        DAGSTER_EXT_ENV_KEYS["context"]: encode_env_var(context_injector_params),
        DAGSTER_EXT_ENV_KEYS["messages"]: encode_env_var(message_reader_params),
    }


@dataclass
class ExtOrchestrationContext:
    context_data: ExtContextData
    message_handler: ExtMessageHandler
    context_injector_params: ExtParams
    message_reader_params: ExtParams

    def get_external_process_env_vars(self):
        return {
            DAGSTER_EXT_ENV_KEYS[IS_DAGSTER_EXT_PROCESS_ENV_VAR]: encode_env_var(True),
            **_ext_params_as_env_vars(
                context_injector_params=self.context_injector_params,
                message_reader_params=self.message_reader_params,
            ),
        }


def build_external_execution_context_data(
    context: OpExecutionContext,
    extras: Optional[ExtExtras],
) -> "ExtContextData":
    asset_keys = (
        [_convert_asset_key(key) for key in sorted(context.selected_asset_keys)]
        if context.has_assets_def
        else None
    )
    code_version_by_asset_key = (
        {
            _convert_asset_key(key): context.assets_def.code_versions_by_key[key]
            for key in context.selected_asset_keys
        }
        if context.has_assets_def
        else None
    )
    provenance_by_asset_key = (
        {
            _convert_asset_key(key): _convert_data_provenance(context.get_asset_provenance(key))
            for key in context.selected_asset_keys
        }
        if context.has_assets_def
        else None
    )
    partition_key = context.partition_key if context.has_partition_key else None
    partition_time_window = context.partition_time_window if context.has_partition_key else None
    partition_key_range = context.partition_key_range if context.has_partition_key else None
    return ExtContextData(
        asset_keys=asset_keys,
        code_version_by_asset_key=code_version_by_asset_key,
        provenance_by_asset_key=provenance_by_asset_key,
        partition_key=partition_key,
        partition_key_range=(
            _convert_partition_key_range(partition_key_range) if partition_key_range else None
        ),
        partition_time_window=(
            _convert_time_window(partition_time_window) if partition_time_window else None
        ),
        run_id=context.run_id,
        job_name=None if isinstance(context, BoundOpExecutionContext) else context.job_name,
        retry_number=0 if isinstance(context, BoundOpExecutionContext) else context.retry_number,
        extras=extras or {},
    )


def _convert_asset_key(asset_key: AssetKey) -> str:
    return asset_key.to_user_string()


def _convert_data_provenance(
    provenance: Optional[DataProvenance],
) -> Optional["ExtDataProvenance"]:
    return (
        None
        if provenance is None
        else ExtDataProvenance(
            code_version=provenance.code_version,
            input_data_versions={
                _convert_asset_key(k): v.value for k, v in provenance.input_data_versions.items()
            },
            is_user_provided=provenance.is_user_provided,
        )
    )


def _convert_time_window(
    time_window: TimeWindow,
) -> "ExtTimeWindow":
    return ExtTimeWindow(
        start=time_window.start.isoformat(),
        end=time_window.end.isoformat(),
    )


def _convert_partition_key_range(
    partition_key_range: PartitionKeyRange,
) -> "ExtTimeWindow":
    return ExtTimeWindow(
        start=partition_key_range.start,
        end=partition_key_range.end,
    )
