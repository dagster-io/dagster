import datetime
import os
from collections.abc import Iterator, Sequence
from typing import Any, Optional

import pytest
from dagster import AssetCheckKey, AssetCheckSeverity, AssetKey, JsonMetadataValue, define_asset_job
from dagster._core.definitions.asset_check_factories.utils import (
    FRESHNESS_PARAMS_METADATA_KEY,
    TIMEZONE_PARAM_KEY,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import freeze_time
from dagster._time import create_datetime, get_current_timestamp
from dagster_dbt import DbtProject, dbt_assets
from dagster_dbt.source_freshness_builder import (
    DBT_FRESHNESS_ERROR_LOWER_BOUND_DELTA_PARAM_KEY,
    DBT_FRESHNESS_WARN_LOWER_BOUND_DELTA_PARAM_KEY,
    _build_dbt_freshness_multi_check,
    build_freshness_checks_from_dbt_source_freshness,
)

from dagster_dbt_tests.dbt_projects import test_dbt_source_freshness_path


@pytest.fixture(name="test_dbt_source_freshness_project", scope="session")
def test_dbt_source_freshness_project() -> DbtProject:
    """Fixture to create a dbt project for testing freshness checks."""
    return DbtProject(
        project_dir=os.fspath(test_dbt_source_freshness_path),
        profiles_dir=os.fspath(test_dbt_source_freshness_path),
    )


@pytest.fixture(name="instance")
def instance_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test() as instance:
        yield instance


def test_dbt_source_freshness_checks(
    test_dbt_source_freshness_manifest: dict[str, Any],
    test_dbt_source_freshness_project: DbtProject,
) -> None:
    @dbt_assets(
        manifest=test_dbt_source_freshness_manifest, project=test_dbt_source_freshness_project
    )
    def my_dbt_assets(): ...

    freshness_checks = build_freshness_checks_from_dbt_source_freshness(
        dbt_project=test_dbt_source_freshness_project, dbt_assets=my_dbt_assets
    )
    # We added a freshness check to the customers table only.
    assert len(freshness_checks) == 1
    freshness_check = freshness_checks[0]
    assert list(freshness_check.check_keys)[0] == AssetCheckKey(  # noqa
        AssetKey(["jaffle_shop", "raw_customers"]), "freshness_check"
    )
    check_metadata = (
        freshness_checks[0]
        .check_specs_by_output_name["jaffle_shop__raw_customers_freshness_check"]
        .metadata
    )
    assert check_metadata
    assert check_metadata[FRESHNESS_PARAMS_METADATA_KEY] == JsonMetadataValue(
        {
            TIMEZONE_PARAM_KEY: "UTC",
            DBT_FRESHNESS_WARN_LOWER_BOUND_DELTA_PARAM_KEY: 43200,
            DBT_FRESHNESS_ERROR_LOWER_BOUND_DELTA_PARAM_KEY: 86400,
        }
    )


def add_new_event(
    instance: DagsterInstance,
    asset_key: AssetKey,
    override_timestamp: Optional[float] = None,
):
    """Helper to add a materialization event for an asset."""
    from dagster._core.definitions.events import AssetMaterialization
    from dagster._core.definitions.metadata import TimestampMetadataValue

    instance.report_runless_asset_event(
        AssetMaterialization(
            asset_key=asset_key,
            metadata={
                "dagster/last_updated_timestamp": TimestampMetadataValue(
                    override_timestamp
                    if override_timestamp is not None
                    else get_current_timestamp()
                )
            },
        )
    )


def execute_check_for_asset(
    assets: list,
    asset_checks: Sequence[AssetChecksDefinition],
    instance: DagsterInstance,
) -> ExecuteInProcessResult:
    """Helper to execute an asset check job."""
    from dagster._core.definitions.source_asset import SourceAsset

    # Make sure assets are actual assets, not just keys
    asset_objects = []
    for asset in assets:
        if isinstance(asset, AssetKey):
            asset_objects.append(SourceAsset(key=asset))
        else:
            asset_objects.append(asset)

    the_job = define_asset_job(
        name="test_asset_job",
        selection=AssetSelection.checks(*asset_checks),
    )

    defs = Definitions(assets=asset_objects, asset_checks=asset_checks, jobs=[the_job])
    job_def = defs.get_job_def("test_asset_job")
    return job_def.execute_in_process(instance=instance)


def assert_check_result(
    the_asset: AssetKey,
    instance: DagsterInstance,
    freshness_checks: Sequence[AssetChecksDefinition],
    severity: AssetCheckSeverity,
    expected_pass: bool,
    description_match: Optional[str] = None,
    metadata_match: Optional[dict] = None,
) -> None:
    """Helper to assert properties of a freshness check result."""
    result = execute_check_for_asset(
        assets=[the_asset],
        asset_checks=freshness_checks,
        instance=instance,
    )
    assert result.success
    assert len(result.get_asset_check_evaluations()) == 1

    # Find evaluation for the asset
    eval_for_asset = None
    for evalu in result.get_asset_check_evaluations():
        if evalu.asset_key == the_asset:
            eval_for_asset = evalu
            break

    assert eval_for_asset is not None, f"No evaluation found for asset {the_asset}"
    assert eval_for_asset.passed == expected_pass
    assert eval_for_asset.severity == severity

    if description_match:
        description = eval_for_asset.description
        assert description
        assert description_match in description

    if metadata_match:
        metadata = eval_for_asset.metadata
        assert metadata
        assert metadata == metadata_match


def test_dbt_freshness_check_no_events(instance: DagsterInstance) -> None:
    """Test that the freshness check fails when there are no events."""
    from dagster._core.definitions.source_asset import SourceAsset

    asset_key = AssetKey(["test_source"])
    source_asset = SourceAsset(key=asset_key)

    # Create a check with warn after 12 hours, error after 24 hours
    warn_delta = datetime.timedelta(hours=12)
    error_delta = datetime.timedelta(hours=24)

    freshness_check = _build_dbt_freshness_multi_check(
        asset_keys=[asset_key],
        blocking=False,
        warn_lower_bound_delta=warn_delta,
        error_lower_bound_delta=error_delta,
    )

    # With no events, check should fail with ERROR severity
    with freeze_time(create_datetime(2023, 1, 1, 12, 0, 0)):
        assert_check_result(
            source_asset.key,
            instance,
            [freshness_check],
            severity=AssetCheckSeverity.ERROR,
            expected_pass=False,
            description_match="Asset has never been observed",
        )


def test_dbt_freshness_check_fresh_event(instance: DagsterInstance) -> None:
    """Test that the freshness check passes when there is a fresh event."""
    from dagster._core.definitions.source_asset import SourceAsset

    asset_key = AssetKey(["test_source"])
    source_asset = SourceAsset(key=asset_key)

    # Create a check with warn after 12 hours, error after 24 hours
    warn_delta = datetime.timedelta(hours=12)
    error_delta = datetime.timedelta(hours=24)

    freshness_check = _build_dbt_freshness_multi_check(
        asset_keys=[asset_key],
        blocking=False,
        warn_lower_bound_delta=warn_delta,
        error_lower_bound_delta=error_delta,
    )

    # Current time is 2023-01-01 12:00:00
    current_time = create_datetime(2023, 1, 1, 12, 0, 0)

    # Add an event 6 hours ago (well within both thresholds)
    with freeze_time(current_time - datetime.timedelta(hours=6)):
        add_new_event(instance, asset_key)

    # Check should pass
    with freeze_time(current_time):
        assert_check_result(
            source_asset.key,
            instance,
            [freshness_check],
            severity=AssetCheckSeverity.ERROR,  # Even though it passes, the severity level is ERROR
            expected_pass=True,
            description_match="Asset is currently fresh",
        )


def test_dbt_freshness_check_warn_threshold(instance: DagsterInstance) -> None:
    """Test check with WARN severity when a check is outside warn threshold but inside error threshold."""
    from dagster._core.definitions.source_asset import SourceAsset

    asset_key = AssetKey(["test_source"])
    source_asset = SourceAsset(key=asset_key)

    # Create a check with warn after 12 hours, error after 24 hours
    warn_delta = datetime.timedelta(hours=12)
    error_delta = datetime.timedelta(hours=24)

    freshness_check = _build_dbt_freshness_multi_check(
        asset_keys=[asset_key],
        blocking=False,
        warn_lower_bound_delta=warn_delta,
        error_lower_bound_delta=error_delta,
    )

    # Current time is 2023-01-01 12:00:00
    current_time = create_datetime(2023, 1, 1, 12, 0, 0)

    # Add an event 18 hours ago (outside warn threshold but inside error threshold)
    with freeze_time(current_time - datetime.timedelta(hours=18)):
        add_new_event(instance, asset_key)

    # Check should fail with WARN severity
    with freeze_time(current_time):
        assert_check_result(
            source_asset.key,
            instance,
            [freshness_check],
            severity=AssetCheckSeverity.WARN,
            expected_pass=False,
            description_match="Asset is overdue for an update",
        )


def test_dbt_freshness_check_error_threshold(instance: DagsterInstance) -> None:
    """Test check with ERROR severity when a check is outside error threshold."""
    from dagster._core.definitions.source_asset import SourceAsset

    asset_key = AssetKey(["test_source"])
    source_asset = SourceAsset(key=asset_key)

    # Create a check with warn after 12 hours, error after 24 hours
    warn_delta = datetime.timedelta(hours=12)
    error_delta = datetime.timedelta(hours=24)

    freshness_check = _build_dbt_freshness_multi_check(
        asset_keys=[asset_key],
        blocking=False,
        warn_lower_bound_delta=warn_delta,
        error_lower_bound_delta=error_delta,
    )

    # Current time is 2023-01-01 12:00:00
    current_time = create_datetime(2023, 1, 1, 12, 0, 0)

    # Add an event 30 hours ago (outside both thresholds)
    with freeze_time(current_time - datetime.timedelta(hours=30)):
        add_new_event(instance, asset_key)

    # Check should fail with ERROR severity
    with freeze_time(current_time):
        assert_check_result(
            source_asset.key,
            instance,
            [freshness_check],
            severity=AssetCheckSeverity.ERROR,
            expected_pass=False,
            description_match="Asset is overdue for an update",
        )


def test_dbt_freshness_check_blocking(instance: DagsterInstance) -> None:
    """Test that the blocking parameter works correctly."""
    from dagster._core.definitions.source_asset import SourceAsset
    from dagster._core.errors import DagsterAssetCheckFailedError

    asset_key = AssetKey(["test_source"])
    source_asset = SourceAsset(key=asset_key)

    # Create a check with warn after 12 hours, error after 24 hours, and blocking=True
    warn_delta = datetime.timedelta(hours=12)
    error_delta = datetime.timedelta(hours=24)

    freshness_check = _build_dbt_freshness_multi_check(
        asset_keys=[asset_key],
        blocking=True,  # This should make the check blocking
        warn_lower_bound_delta=warn_delta,
        error_lower_bound_delta=error_delta,
    )

    # Current time is 2023-01-01 12:00:00
    current_time = create_datetime(2023, 1, 1, 12, 0, 0)

    # Add an event outside error threshold
    with freeze_time(current_time - datetime.timedelta(hours=30)):
        add_new_event(instance, asset_key)

    # Execute the check - it should fail because the check is blocking and fails
    with freeze_time(current_time):
        try:
            execute_check_for_asset(
                [source_asset.key],
                [freshness_check],
                instance,
            )
            raise AssertionError("Expected job to fail with DagsterAssetCheckFailedError")
        except DagsterAssetCheckFailedError as e:
            # This is expected - the job fails when a blocking check fails
            assert "Blocking check 'freshness_check' for asset 'test_source' failed" in str(e)
            assert "ERROR severity" in str(e)
