import responses
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_ENVIRONMENT_ID,
    TEST_JOB_ID,
    TEST_PROJECT_ID,
    get_sample_manifest_json,
)


def test_fetch_dbt_cloud_workspace_data(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    workspace_data = workspace.fetch_workspace_data()
    assert workspace_data.project_id == TEST_PROJECT_ID
    assert workspace_data.environment_id == TEST_ENVIRONMENT_ID
    assert workspace_data.job_id == TEST_JOB_ID
    assert workspace_data.manifest == get_sample_manifest_json()


def test_load_asset_specs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_assets = workspace.load_asset_specs()
    all_assets_keys = [asset.key for asset in all_assets]

    # 8 dbt models
    assert len(all_assets) == 8
    assert len(all_assets_keys) == 8

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customers"]
    first_asset_kinds = next(spec.kinds for spec in sorted(all_assets))
    assert "dbtcloud" in first_asset_kinds
    assert "dbt" not in first_asset_kinds

    # Clearing cache for other tests
    workspace.load_specs.cache_clear()


def test_load_check_specs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_checks = workspace.load_check_specs()
    all_checks_keys = [check.key for check in all_checks]

    # 8 dbt models
    assert len(all_checks) == 20
    assert len(all_checks_keys) == 20

    # Sanity check outputs
    first_check_key = next(key for key in sorted(all_checks_keys))
    assert first_check_key.name == "not_null_customers_customer_id"
    assert first_check_key.asset_key.path == ["customers"]

    # Clearing cache for other tests
    workspace.load_specs.cache_clear()
