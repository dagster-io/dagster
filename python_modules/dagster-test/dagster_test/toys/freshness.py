import time
from typing import cast

from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    DataVersion,
    Definitions,
    SourceAsset,
    asset_check,
    observable_source_asset,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.data_version import DATA_TIME_TAG
from dagster._core.events import AssetObservationData


@observable_source_asset
def foo():
    return DataVersion("1", time.time())


def build_freshness_check(asset: SourceAsset, maximum_lag_minutes: float):
    @asset_check(asset=asset)
    def freshness_check(context: AssetExecutionContext):
        observations = context.instance.event_log_storage.fetch_observations(
            records_filter=asset.key, limit=1
        ).records
        if not observations:
            return AssetCheckResult(
                passed=False,
                metadata={"error": "No observations found for asset."},
                severity=AssetCheckSeverity.WARN,
            )

        last_updated = cast(
            AssetObservationData, observations[0].event_log_entry.dagster_event.event_specific_data
        ).asset_observation.tags.get(DATA_TIME_TAG)

        if not last_updated:
            return AssetCheckResult(
                passed=False,
                metadata={"error": "No data time tag found for asset."},
                severity=AssetCheckSeverity.WARN,
            )

        minutes_since_last_updated = int((time.time() - float(last_updated)) / 60)
        return AssetCheckResult(
            passed=minutes_since_last_updated <= maximum_lag_minutes,
            metadata={"minutes_since_last_updated": minutes_since_last_updated},
        )

    return freshness_check


defs = Definitions(
    assets=[foo],
    asset_checks=[build_freshness_check(foo, maximum_lag_minutes=1)],
)
