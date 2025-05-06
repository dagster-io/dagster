import datetime
from collections.abc import Iterable, Sequence
from typing import Any, Optional

from dagster import (
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetKey,
    AssetsDefinition,
    JsonMetadataValue,
    MetadataValue,
    TimestampMetadataValue,
)
from dagster._annotations import beta
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    construct_description,
)
from dagster._core.definitions.asset_check_factories.utils import (
    DEFAULT_FRESHNESS_TIMEZONE,
    FRESH_UNTIL_METADATA_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    LAST_UPDATED_TIMESTAMP_METADATA_KEY,
    LOWER_BOUND_TIMESTAMP_METADATA_KEY,
    TIMEZONE_PARAM_KEY,
    freshness_multi_asset_check,
    retrieve_last_update_record,
    retrieve_timestamp_from_record,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._time import get_current_timestamp, get_timezone
from dagster_shared import check

from dagster_dbt import DbtProject
from dagster_dbt.asset_utils import get_manifest_and_translator_from_dbt_assets

try:
    from dbt.artifacts.resources.v1.components import (
        FreshnessThreshold,  # pyright: ignore [reportAttributeAccessIssue]
    )
except ImportError:
    from dbt.contracts.graph.unparsed import (
        FreshnessThreshold,  # pyright: ignore [reportAttributeAccessIssue]
    )


DBT_FRESHNESS_WARN_LOWER_BOUND_DELTA_PARAM_KEY = "dbt_freshness_warn_lower_bound_delta_seconds"
DBT_FRESHNESS_ERROR_LOWER_BOUND_DELTA_PARAM_KEY = "dbt_freshness_error_lower_bound_delta_seconds"


def _dbt_freshness_as_timedelta(count: int, period: str) -> datetime.timedelta:
    """Converts dbt freshness configuration to seconds."""
    if period == "minute":
        return datetime.timedelta(minutes=count)
    elif period == "hour":
        return datetime.timedelta(hours=count)
    elif period == "day":
        return datetime.timedelta(days=count)
    else:
        raise ValueError(f"Unsupported period: {period}. Supported periods are: minute, hour, day.")


@beta
def build_freshness_checks_from_dbt_source_freshness(
    dbt_project: DbtProject,
    dbt_assets: AssetsDefinition,
    blocking: bool = False,
) -> Sequence[AssetChecksDefinition]:
    """Returns a sequence of freshness checks constructed from dbt source freshness configuration.

    This function extracts freshness configuration from dbt sources in your project and creates
    corresponding Dagster asset checks. It leverages the native dbt source freshness configuration
    to automatically generate asset checks with appropriate warning and error thresholds.

    Freshness checks are configured directly in your dbt sources schema configuration using
    the standard dbt freshness syntax. Both warn_after and error_after configurations are supported.

    Below is an example of configuring a dbt source with freshness checks.
    This code would be placed in the schema.yml file for the dbt source:

    .. code-block:: YAML

        sources:
          - name: raw_data
            tables:
              - name: customers
                freshness:
                  warn_after:
                    count: 12
                    period: hour
                  error_after:
                    count: 24
                    period: hour

    Supported periods are 'minute', 'hour', and 'day'. The function converts these to appropriate
    timedelta values and creates last_update freshness checks with the corresponding severity levels.

    Args:
        dbt_project (DbtProject): The dbt project to extract freshness configuration from.
        dbt_assets (AssetsDefinition): The dbt assets definition that belongs to the same DBT
            project as the sources to build freshness checks for. This is needed to properly
            translate between dbt sources and Dagster asset keys.

    Returns:
        Sequence[AssetChecksDefinition]: A sequence of asset checks definitions representing the
            freshness checks for the dbt sources with configured freshness criteria.
    """
    freshness_checks: list[AssetChecksDefinition] = []
    manifest, translator = get_manifest_and_translator_from_dbt_assets([dbt_assets])
    freshness_to_asset_keys: dict[
        tuple[Optional[datetime.timedelta], Optional[datetime.timedelta]], list[AssetKey]
    ] = {}

    for node in manifest["sources"].values():
        freshness = FreshnessThreshold.from_dict(node.get("freshness", {}))
        if node["resource_type"] != "source" or not freshness:
            continue
        asset_spec = translator.get_asset_spec(manifest, node["unique_id"], dbt_project)

        warn_lower_bound_delta = (
            _dbt_freshness_as_timedelta(freshness.warn_after.count, freshness.warn_after.period)
            if freshness.warn_after
            else None
        )
        error_lower_bound_delta = (
            _dbt_freshness_as_timedelta(freshness.error_after.count, freshness.error_after.period)
            if freshness.error_after
            else None
        )

        freshness_to_asset_keys.setdefault(
            (warn_lower_bound_delta, error_lower_bound_delta), []
        ).append(asset_spec.key)

    for (
        warn_lower_bound_delta,
        error_lower_bound_delta,
    ), asset_keys in freshness_to_asset_keys.items():
        freshness_checks.append(
            _build_dbt_freshness_multi_check(
                asset_keys=asset_keys,
                blocking=blocking,
                warn_lower_bound_delta=warn_lower_bound_delta,
                error_lower_bound_delta=error_lower_bound_delta,
            )
        )

    return freshness_checks


def _build_dbt_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    blocking: bool,
    warn_lower_bound_delta: Optional[datetime.timedelta] = None,
    error_lower_bound_delta: Optional[datetime.timedelta] = None,
    timezone: str = DEFAULT_FRESHNESS_TIMEZONE,
) -> AssetChecksDefinition:
    params_metadata: dict[str, Any] = {
        TIMEZONE_PARAM_KEY: timezone,
        DBT_FRESHNESS_WARN_LOWER_BOUND_DELTA_PARAM_KEY: warn_lower_bound_delta.total_seconds()
        if warn_lower_bound_delta
        else None,
        DBT_FRESHNESS_ERROR_LOWER_BOUND_DELTA_PARAM_KEY: error_lower_bound_delta.total_seconds()
        if error_lower_bound_delta
        else None,
    }

    @freshness_multi_asset_check(
        params_metadata=JsonMetadataValue(params_metadata), asset_keys=asset_keys, blocking=blocking
    )
    def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
        for check_key in context.selected_asset_check_keys:
            asset_key = check_key.asset_key
            current_timestamp = get_current_timestamp()
            current_time_in_freshness_tz = datetime.datetime.fromtimestamp(
                current_timestamp, tz=get_timezone(timezone)
            )

            # Calculate both lower bounds
            warn_time_lower_bound = None
            if warn_lower_bound_delta:
                warn_time_lower_bound = current_time_in_freshness_tz - warn_lower_bound_delta

            error_time_lower_bound = None
            if error_lower_bound_delta:
                error_time_lower_bound = current_time_in_freshness_tz - error_lower_bound_delta

            # Retrieve the last update record
            latest_record = retrieve_last_update_record(
                instance=context.instance, asset_key=asset_key, partition_key=None
            )
            update_timestamp = (
                retrieve_timestamp_from_record(latest_record) if latest_record else None
            )

            # Determine if check passes and what severity to use
            passed = True
            severity: AssetCheckSeverity = AssetCheckSeverity.ERROR

            # Determine the most restrictive lower bound for metadata
            metadata_lower_bound = None
            if update_timestamp is not None:
                if error_lower_bound_delta and error_time_lower_bound:
                    if update_timestamp < error_time_lower_bound.timestamp():
                        passed = False
                        severity = AssetCheckSeverity.ERROR
                        metadata_lower_bound = error_time_lower_bound
                    elif (
                        warn_lower_bound_delta
                        and warn_time_lower_bound
                        and update_timestamp < warn_time_lower_bound.timestamp()
                    ):
                        passed = False
                        severity = AssetCheckSeverity.WARN
                        metadata_lower_bound = warn_time_lower_bound
                    else:
                        metadata_lower_bound = (
                            warn_time_lower_bound
                            if warn_time_lower_bound
                            else error_time_lower_bound
                        )
                elif warn_lower_bound_delta and warn_time_lower_bound:
                    if update_timestamp < warn_time_lower_bound.timestamp():
                        passed = False
                        severity = AssetCheckSeverity.WARN
                    metadata_lower_bound = warn_time_lower_bound
            else:
                # No update timestamp means it fails at the highest severity
                passed = False
                severity = (
                    AssetCheckSeverity.ERROR if error_lower_bound_delta else AssetCheckSeverity.WARN
                )
                metadata_lower_bound = (
                    error_time_lower_bound if error_time_lower_bound else warn_time_lower_bound
                )

            # Build metadata
            metadata: dict[str, MetadataValue] = {
                FRESHNESS_PARAMS_METADATA_KEY: JsonMetadataValue(params_metadata),
            }

            if metadata_lower_bound:
                metadata[LOWER_BOUND_TIMESTAMP_METADATA_KEY] = TimestampMetadataValue(
                    metadata_lower_bound.timestamp()
                )

            if passed and update_timestamp and warn_lower_bound_delta:
                # Calculate when the asset will become stale
                fresh_until = (
                    check.not_none(update_timestamp) + warn_lower_bound_delta.total_seconds()
                )
                metadata[FRESH_UNTIL_METADATA_KEY] = TimestampMetadataValue(fresh_until)

            if update_timestamp:
                metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY] = TimestampMetadataValue(
                    update_timestamp
                )

            yield AssetCheckResult(
                passed=passed,
                description=construct_description(
                    passed,
                    last_update_time_lower_bound=metadata_lower_bound.timestamp()
                    if metadata_lower_bound
                    else None,
                    current_timestamp=current_timestamp,
                    update_timestamp=update_timestamp,
                ),
                severity=severity,
                asset_key=asset_key,
                metadata=metadata,
            )

    return the_check
