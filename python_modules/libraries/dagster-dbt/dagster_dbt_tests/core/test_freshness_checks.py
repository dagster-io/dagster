from datetime import datetime
from typing import Any, Dict

import pytest
from dagster import AssetKey, DailyPartitionsDefinition
from dagster._check import CheckError
from dagster._core.definitions.asset_check_factories.utils import (
    DEADLINE_CRON_PARAM_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    LOWER_BOUND_DELTA_PARAM_KEY,
    TIMEZONE_PARAM_KEY,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.freshness_builder import build_freshness_checks_from_dbt_assets


def test_dbt_last_update_freshness_checks(
    test_last_update_freshness_manifest: dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_last_update_freshness_manifest)
    def my_dbt_assets(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(dbt_assets=[my_dbt_assets])
    # We added a freshness check to the customers table only.
    assert len(freshness_checks) == 1
    freshness_check = freshness_checks[0]
    assert list(freshness_check.check_keys)[0] == AssetCheckKey(  # noqa
        AssetKey("customers"), "freshness_check"
    )
    check_metadata = (
        freshness_checks[0].check_specs_by_output_name["customers_freshness_check"].metadata
    )
    assert check_metadata
    assert check_metadata[FRESHNESS_PARAMS_METADATA_KEY] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            LOWER_BOUND_DELTA_PARAM_KEY: 86400,
            DEADLINE_CRON_PARAM_KEY: "0 0 * * *",
        }
    )


def test_dbt_time_partition_freshness_checks(
    test_time_partition_freshness_manifest: dict[str, Any],
) -> None:
    @dbt_assets(
        manifest=test_time_partition_freshness_manifest,
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(dbt_assets=[my_dbt_assets])
    freshness_check = freshness_checks[0]
    # We added a freshness check to the customers table only.
    assert len(freshness_checks) == 1
    assert list(freshness_check.check_keys)[0] == AssetCheckKey(  # noqa
        AssetKey("customers"), "freshness_check"
    )
    check_metadata = (
        freshness_checks[0].check_specs_by_output_name["customers_freshness_check"].metadata
    )
    assert check_metadata
    assert check_metadata[FRESHNESS_PARAMS_METADATA_KEY] == JsonMetadataValue(
        {TIMEZONE_PARAM_KEY: "UTC", DEADLINE_CRON_PARAM_KEY: "0 0 * * *"}
    )


def test_dbt_duplicate_assets_defs(test_last_update_freshness_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_last_update_freshness_manifest)
    def my_dbt_assets(): ...

    with pytest.raises(CheckError):
        build_freshness_checks_from_dbt_assets(dbt_assets=[my_dbt_assets, my_dbt_assets])


def test_last_update_multiple_assets_defs(
    test_last_update_freshness_manifest_multiple_assets_defs: dict[str, Any],
) -> None:
    @dbt_assets(
        manifest=test_last_update_freshness_manifest_multiple_assets_defs, select="customers"
    )
    def my_dbt_assets(): ...

    @dbt_assets(manifest=test_last_update_freshness_manifest_multiple_assets_defs, select="orders")
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_assets=[my_dbt_assets, my_dbt_assets2]
    )
    assert len(freshness_checks) == 2

    customers_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["customers"]), name="freshness_check")
        in check.check_keys
    ]
    assert len(customers_checks) == 1
    orders_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["orders"]), name="freshness_check") in check.check_keys
    ]
    assert len(orders_checks) == 1
    customers_check = next(iter(customers_checks))
    orders_check = next(iter(orders_checks))
    assert customers_check.check_specs_by_output_name["customers_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            LOWER_BOUND_DELTA_PARAM_KEY: 86400,
            DEADLINE_CRON_PARAM_KEY: "0 0 * * *",
        }
    )
    assert orders_check.check_specs_by_output_name["orders_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            LOWER_BOUND_DELTA_PARAM_KEY: 86400,
            DEADLINE_CRON_PARAM_KEY: "1 1 * * *",
        }
    )


def test_time_partition_multiple_assets_defs(
    test_time_partition_freshness_manifest_multiple_assets_defs: dict[str, Any],
) -> None:
    @dbt_assets(
        manifest=test_time_partition_freshness_manifest_multiple_assets_defs,
        select="customers",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets(): ...

    @dbt_assets(
        manifest=test_time_partition_freshness_manifest_multiple_assets_defs,
        select="orders",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_assets=[my_dbt_assets, my_dbt_assets2]
    )
    assert len(freshness_checks) == 2

    customers_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["customers"]), name="freshness_check")
        in check.check_keys
    ]
    assert len(customers_checks) == 1
    orders_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["orders"]), name="freshness_check") in check.check_keys
    ]
    assert len(orders_checks) == 1
    customers_check = next(iter(customers_checks))
    orders_check = next(iter(orders_checks))
    assert customers_check.check_specs_by_output_name["customers_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            DEADLINE_CRON_PARAM_KEY: "0 0 * * *",
        }
    )
    assert orders_check.check_specs_by_output_name["orders_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            DEADLINE_CRON_PARAM_KEY: "1 1 * * *",
        }
    )


def test_mixed_freshness(test_dagster_dbt_mixed_freshness_manifest: dict[str, Any]) -> None:
    """Test passing one time-partitioned asset and one last-update asset to the builder."""

    @dbt_assets(manifest=test_dagster_dbt_mixed_freshness_manifest, select="customers")
    def my_dbt_assets(): ...

    @dbt_assets(
        manifest=test_dagster_dbt_mixed_freshness_manifest,
        select="orders",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_assets=[my_dbt_assets, my_dbt_assets2]
    )
    assert len(freshness_checks) == 2

    customers_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["customers"]), name="freshness_check")
        in check.check_keys
    ]
    assert len(customers_checks) == 1
    orders_checks = [
        check
        for check in freshness_checks
        if AssetCheckKey(asset_key=AssetKey(["orders"]), name="freshness_check") in check.check_keys
    ]
    assert len(orders_checks) == 1
    customers_check = next(iter(customers_checks))
    orders_check = next(iter(orders_checks))
    assert customers_check.check_specs_by_output_name["customers_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            LOWER_BOUND_DELTA_PARAM_KEY: 86400,
            DEADLINE_CRON_PARAM_KEY: "0 0 * * *",
        }
    )
    assert orders_check.check_specs_by_output_name["orders_freshness_check"].metadata[  # type: ignore[attr-defined]
        FRESHNESS_PARAMS_METADATA_KEY
    ] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            DEADLINE_CRON_PARAM_KEY: "1 1 * * *",
        }
    )
