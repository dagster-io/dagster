import datetime
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
    AssetCheckSpec,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.decorators.asset_check_decorator import (
    multi_asset_check,
)
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import FloatMetadataValue, TimestampMetadataValue
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext,
)
from dagster._core.instance import DagsterInstance
from dagster._utils.schedules import is_valid_cron_string

from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetKey, CoercibleToAssetKey
from .utils import (
    DEADLINE_CRON_METADATA_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    FRESHNESS_TIMEZONE_METADATA_KEY,
    LOWER_BOUND_DELTA_METADATA_KEY,
    OVERDUE_DEADLINE_TIMESTAMP_METADATA_KEY,
    OVERDUE_SECONDS_METADATA_KEY,
    SEVERITY_METADATA_KEY,
    asset_to_keys_iterable,
    ensure_no_duplicate_assets,
    get_deadline_timestamp,
    get_description_for_freshness_check_result,
    get_last_update_time_lower_bound,
    get_last_updated_timestamp,
    get_latest_complete_partition_key,
    get_overdue_seconds,
    retrieve_latest_record,
    unique_id_from_asset_keys,
)


def build_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    lower_bound_delta: datetime.timedelta,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]],
) -> AssetChecksDefinition:
    params_metadata: dict[str, Any] = {
        FRESHNESS_TIMEZONE_METADATA_KEY: timezone,
        SEVERITY_METADATA_KEY: severity.value,
    }
    if deadline_cron:
        params_metadata[DEADLINE_CRON_METADATA_KEY] = deadline_cron
    if lower_bound_delta:
        params_metadata[LOWER_BOUND_DELTA_METADATA_KEY] = lower_bound_delta.total_seconds()

    @multi_asset_check(
        specs=[
            AssetCheckSpec(
                "freshness_check",
                asset=asset_key,
                metadata={FRESHNESS_PARAMS_METADATA_KEY: params_metadata},
                description="Evaluates freshness for targeted asset.",
            )
            for asset_key in asset_keys
        ],
        can_subset=True,
        name=f"freshness_check_{unique_id_from_asset_keys(asset_keys)}",
    )
    def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
        for check_key in context.selected_asset_check_keys:
            if asset_property_enforcement_lambda:
                asset_property_enforcement_lambda(
                    context.job_def.asset_layer.asset_graph.get(check_key.asset_key).assets_def
                )
            yield evaluate_freshness_check(check_key, context.job_def, context.instance)

    return the_check


def evaluate_freshness_check(
    check_key: AssetCheckKey, job_def: JobDefinition, instance: DagsterInstance
) -> AssetCheckResult:
    asset_key = check_key.asset_key
    asset_node = job_def.asset_layer.asset_graph.get(asset_key)
    asset_checks_def = job_def.asset_layer.assets_defs_by_check_key[check_key]
    check_spec = asset_checks_def.get_spec_for_check_key(check_key)
    current_timestamp = pendulum.now("UTC").timestamp()

    # Explicit call to partitions def here will be replaced with AssetSlice reference once it's available.
    partitions_def = cast(
        Optional[TimeWindowPartitionsDefinition],
        asset_node.partitions_def,
    )
    check.invariant(
        partitions_def is None or isinstance(partitions_def, TimeWindowPartitionsDefinition),
        "Expected partitions_def to be time-windowed.",
    )
    params_metadata = get_metadata(check_spec)[FRESHNESS_PARAMS_METADATA_KEY]
    deadline_cron = get_freshness_cron(get_metadata(check_spec))
    timezone = get_freshness_cron_timezone(get_metadata(check_spec))
    lower_bound_delta = get_lower_bound_delta(get_metadata(check_spec))
    severity = get_severity(get_metadata(check_spec))

    last_update_time_lower_bound = get_last_update_time_lower_bound(
        deadline_cron=deadline_cron,
        timezone=timezone,
        current_timestamp=current_timestamp,
        lower_bound_delta=lower_bound_delta,
    )
    expected_partition_key = get_latest_complete_partition_key(
        deadline_cron=deadline_cron,
        current_timestamp=current_timestamp,
        timezone=timezone,
        partitions_def=partitions_def,
    )
    latest_record = retrieve_latest_record(
        instance=instance, asset_key=asset_key, partition_key=expected_partition_key
    )
    update_timestamp = get_last_updated_timestamp(latest_record)
    passed = (
        update_timestamp is not None
        and update_timestamp >= last_update_time_lower_bound.timestamp()
    )

    deadline_timestamp = get_deadline_timestamp(
        deadline_cron=deadline_cron,
        timezone=timezone,
        current_timestamp=current_timestamp,
        lower_bound_delta=lower_bound_delta,
        last_update_timestamp=update_timestamp,
    )
    metadata = {
        FRESHNESS_PARAMS_METADATA_KEY: params_metadata,
        OVERDUE_DEADLINE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(deadline_timestamp),
    }
    if not passed:
        metadata[OVERDUE_SECONDS_METADATA_KEY] = FloatMetadataValue(
            get_overdue_seconds(
                deadline_timestamp=deadline_timestamp, current_timestamp=current_timestamp
            )
        )

    return AssetCheckResult(
        passed=passed,
        description=get_description_for_freshness_check_result(
            passed,
            update_timestamp,
            last_update_time_lower_bound,
            current_timestamp,
            expected_partition_key,
        ),
        severity=severity,
        asset_key=asset_key,
        metadata=metadata,
    )


def build_freshness_checks_for_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]] = None,
    lower_bound_delta: datetime.timedelta = datetime.timedelta(minutes=0),
) -> AssetChecksDefinition:
    ensure_no_duplicate_assets(assets)
    deadline_cron = check.opt_str_param(deadline_cron, "deadline_cron")
    check.invariant(
        is_valid_cron_string(deadline_cron) if deadline_cron else True,
        "deadline_cron must be a valid cron string.",
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    timezone = check.str_param(timezone, "timezone")
    lower_bound_delta = check.inst_param(lower_bound_delta, "lower_bound_delta", datetime.timedelta)

    return build_freshness_multi_check(
        asset_keys=[asset_key for asset in assets for asset_key in asset_to_keys_iterable(asset)],
        deadline_cron=deadline_cron,
        timezone=timezone,
        severity=severity,
        lower_bound_delta=lower_bound_delta,
        asset_property_enforcement_lambda=asset_property_enforcement_lambda,
    )


def get_metadata(check_spec: AssetCheckSpec) -> Mapping[str, Any]:
    if check_spec.metadata:
        return check_spec.metadata
    check.assert_never(check_spec.metadata)


def get_freshness_cron(metadata: Mapping[str, Any]) -> Optional[str]:
    return metadata[FRESHNESS_PARAMS_METADATA_KEY].get(DEADLINE_CRON_METADATA_KEY)


def get_severity(metadata: Mapping[str, Any]) -> AssetCheckSeverity:
    return AssetCheckSeverity(metadata[FRESHNESS_PARAMS_METADATA_KEY][SEVERITY_METADATA_KEY])


def get_freshness_cron_timezone(metadata: Mapping[str, Any]) -> str:
    return metadata[FRESHNESS_PARAMS_METADATA_KEY][FRESHNESS_TIMEZONE_METADATA_KEY]


def get_lower_bound_delta(metadata: Mapping[str, Any]) -> datetime.timedelta:
    float_delta: float = metadata[FRESHNESS_PARAMS_METADATA_KEY].get(LOWER_BOUND_DELTA_METADATA_KEY)
    return datetime.timedelta(seconds=float_delta) if float_delta else datetime.timedelta(seconds=0)
