import os
from datetime import datetime
from typing import Any

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
from dagster_dbt import DbtProject
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.freshness_builder import build_freshness_checks_from_dbt_assets

from dagster_dbt_tests.dbt_projects import (
    test_dagster_dbt_mixed_freshness_path,
    test_last_update_freshness_multiple_assets_defs_path,
    test_last_update_freshness_path,
    test_time_partition_freshness_multiple_assets_defs_path,
    test_time_partition_freshness_path,
)


@pytest.fixture(name="test_last_update_freshness_project", scope="session")
def test_last_update_freshness_project() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_last_update_freshness_path),
        profiles_dir=os.fspath(test_last_update_freshness_path),
    )


@pytest.fixture(name="test_time_partition_freshness_project", scope="session")
def test_time_partition_freshness_project() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_time_partition_freshness_path),
        profiles_dir=os.fspath(test_time_partition_freshness_path),
    )


@pytest.fixture(name="test_last_update_freshness_project_multiple_assets_defs", scope="session")
def test_last_update_freshness_project_multiple_assets_defs() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_last_update_freshness_multiple_assets_defs_path),
        profiles_dir=os.fspath(test_last_update_freshness_multiple_assets_defs_path),
    )


@pytest.fixture(name="test_time_partition_freshness_project_multiple_assets_defs", scope="session")
def test_time_partition_freshness_project_multiple_assets_defs() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_time_partition_freshness_multiple_assets_defs_path),
        profiles_dir=os.fspath(test_time_partition_freshness_multiple_assets_defs_path),
    )


@pytest.fixture(name="test_dagster_dbt_mixed_freshness_project", scope="session")
def test_dagster_dbt_mixed_freshness_project() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_dagster_dbt_mixed_freshness_path),
        profiles_dir=os.fspath(test_dagster_dbt_mixed_freshness_path),
    )


def test_dbt_last_update_freshness_checks(
    test_last_update_freshness_manifest: dict[str, Any],
    test_last_update_freshness_project: DbtProject,
) -> None:
    @dbt_assets(
        manifest=test_last_update_freshness_manifest, project=test_last_update_freshness_project
    )
    def my_dbt_assets(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_project=test_last_update_freshness_project, dbt_assets=[my_dbt_assets]
    )
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
    test_time_partition_freshness_project: DbtProject,
) -> None:
    @dbt_assets(
        manifest=test_time_partition_freshness_manifest,
        project=test_time_partition_freshness_project,
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_project=test_time_partition_freshness_project, dbt_assets=[my_dbt_assets]
    )
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


def test_dbt_duplicate_assets_defs(
    test_last_update_freshness_manifest: dict[str, Any],
    test_last_update_freshness_project: DbtProject,
) -> None:
    @dbt_assets(
        manifest=test_last_update_freshness_manifest, project=test_last_update_freshness_project
    )
    def my_dbt_assets(): ...

    with pytest.raises(CheckError):
        build_freshness_checks_from_dbt_assets(
            dbt_project=test_last_update_freshness_project,
            dbt_assets=[my_dbt_assets, my_dbt_assets],
        )


def test_last_update_multiple_assets_defs(
    test_last_update_freshness_manifest_multiple_assets_defs: dict[str, Any],
    test_last_update_freshness_project_multiple_assets_defs: DbtProject,
) -> None:
    @dbt_assets(
        project=test_last_update_freshness_project_multiple_assets_defs,
        manifest=test_last_update_freshness_manifest_multiple_assets_defs,
        select="customers",
    )
    def my_dbt_assets(): ...

    @dbt_assets(
        project=test_last_update_freshness_project_multiple_assets_defs,
        manifest=test_last_update_freshness_manifest_multiple_assets_defs,
        select="orders",
    )
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_project=test_last_update_freshness_project_multiple_assets_defs,
        dbt_assets=[my_dbt_assets, my_dbt_assets2],
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
    test_time_partition_freshness_project_multiple_assets_defs: DbtProject,
) -> None:
    @dbt_assets(
        manifest=test_time_partition_freshness_manifest_multiple_assets_defs,
        project=test_time_partition_freshness_project_multiple_assets_defs,
        select="customers",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets(): ...

    @dbt_assets(
        manifest=test_time_partition_freshness_manifest_multiple_assets_defs,
        project=test_time_partition_freshness_project_multiple_assets_defs,
        select="orders",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
    )
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_project=test_time_partition_freshness_project_multiple_assets_defs,
        dbt_assets=[my_dbt_assets, my_dbt_assets2],
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


def test_mixed_freshness(
    test_dagster_dbt_mixed_freshness_manifest: dict[str, Any],
    test_dagster_dbt_mixed_freshness_project: DbtProject,
) -> None:
    """Test passing one time-partitioned asset and one last-update asset to the builder."""

    @dbt_assets(
        manifest=test_dagster_dbt_mixed_freshness_manifest,
        select="customers",
        project=test_dagster_dbt_mixed_freshness_project,
    )
    def my_dbt_assets(): ...

    @dbt_assets(
        manifest=test_dagster_dbt_mixed_freshness_manifest,
        select="orders",
        partitions_def=DailyPartitionsDefinition(start_date=datetime(2021, 1, 1)),
        project=test_dagster_dbt_mixed_freshness_project,
    )
    def my_dbt_assets2(): ...

    freshness_checks = build_freshness_checks_from_dbt_assets(
        dbt_project=test_dagster_dbt_mixed_freshness_project,
        dbt_assets=[my_dbt_assets, my_dbt_assets2],
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
