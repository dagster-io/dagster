from typing import Optional

from dagster_external.protocol import (
    ExternalDataProvenance,
    ExternalExecutionContextData,
    ExternalExecutionExtras,
    ExternalTimeWindow,
)

from dagster._core.definitions.data_version import DataProvenance
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.invocation import BoundOpExecutionContext


def build_external_execution_context(
    context: OpExecutionContext,
    extras: Optional[ExternalExecutionExtras],
) -> "ExternalExecutionContextData":
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
    return ExternalExecutionContextData(
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
) -> Optional["ExternalDataProvenance"]:
    return (
        None
        if provenance is None
        else ExternalDataProvenance(
            code_version=provenance.code_version,
            input_data_versions={
                _convert_asset_key(k): v.value for k, v in provenance.input_data_versions.items()
            },
            is_user_provided=provenance.is_user_provided,
        )
    )


def _convert_time_window(
    time_window: TimeWindow,
) -> "ExternalTimeWindow":
    return ExternalTimeWindow(
        start=time_window.start.isoformat(),
        end=time_window.end.isoformat(),
    )


def _convert_partition_key_range(
    partition_key_range: PartitionKeyRange,
) -> "ExternalTimeWindow":
    return ExternalTimeWindow(
        start=partition_key_range.start,
        end=partition_key_range.end,
    )
