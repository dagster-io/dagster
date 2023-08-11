from typing import Optional

from dagster_external.protocol import (
    ExternalDataProvenance,
    ExternalExecutionContextData,
    ExternalExecutionUserdata,
    ExternalTimeWindow,
)

from dagster._core.definitions.data_version import DataProvenance
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.execution.context.compute import OpExecutionContext


def build_external_execution_context(
    context: OpExecutionContext,
    userdata: Optional[ExternalExecutionUserdata],
) -> "ExternalExecutionContextData":
    asset_key = context.asset_key_for_output()
    asset_provenance = context.get_asset_provenance(asset_key)
    partition_key = context.partition_key if context.has_partition_key else None
    partition_time_window = context.partition_time_window if context.has_partition_key else None
    partition_key_range = context.partition_key_range if context.has_partition_key else None
    return ExternalExecutionContextData(
        asset_key=_convert_asset_key(asset_key),
        code_version=context.job_def.asset_layer.code_version_for_asset(asset_key),
        data_provenance=(_convert_data_provenance(asset_provenance) if asset_provenance else None),
        partition_key=partition_key,
        partition_key_range=(
            _convert_partition_key_range(partition_key_range) if partition_key_range else None
        ),
        partition_time_window=(
            _convert_time_window(partition_time_window) if partition_time_window else None
        ),
        run_id=context.run_id,
        run_tags=context.run_tags,
        job_name=context.job_name,
        retry_number=context.retry_number,
        userdata=userdata or {},
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
