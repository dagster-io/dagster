import responses
from dagster_dbt.cloud_v2.resources import (
    DbtCloudWorkspace,
    load_dbt_cloud_asset_specs,
    load_dbt_cloud_check_specs,
)

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_ADHOC_JOB_ID,
    TEST_ENVIRONMENT_ID,
    TEST_LIST_JOBS,
    TEST_PROJECT_ID,
    get_sample_manifest_json,
)


def test_fetch_dbt_cloud_workspace_data(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    workspace_data = workspace.get_or_fetch_workspace_data()
    assert len(fetch_workspace_data_api_mocks.calls) == 8
    assert workspace_data.project_id == TEST_PROJECT_ID
    assert workspace_data.environment_id == TEST_ENVIRONMENT_ID
    assert workspace_data.adhoc_job_id == TEST_ADHOC_JOB_ID
    assert workspace_data.manifest == get_sample_manifest_json()
    assert workspace_data.jobs == TEST_LIST_JOBS


def test_load_asset_specs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_assets = load_dbt_cloud_asset_specs(workspace=workspace)
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


def test_load_asset_specs_select(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_assets = load_dbt_cloud_asset_specs(workspace=workspace, select="raw_customers+")
    all_assets_keys = [asset.key for asset in all_assets]

    # 3 dbt models
    assert len(all_assets) == 3
    assert len(all_assets_keys) == 3

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customers"]
    first_asset_kinds = next(spec.kinds for spec in sorted(all_assets))
    assert "dbtcloud" in first_asset_kinds
    assert "dbt" not in first_asset_kinds


def test_load_asset_specs_exclude(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_assets = load_dbt_cloud_asset_specs(workspace=workspace, exclude="raw_customers+")
    all_assets_keys = [asset.key for asset in all_assets]

    # 5 dbt models
    assert len(all_assets) == 5
    assert len(all_assets_keys) == 5

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["orders"]
    first_asset_kinds = next(spec.kinds for spec in sorted(all_assets))
    assert "dbtcloud" in first_asset_kinds
    assert "dbt" not in first_asset_kinds


def test_load_asset_specs_selector(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_assets = load_dbt_cloud_asset_specs(
        workspace=workspace, selector="raw_customer_child_models"
    )
    all_assets_keys = [asset.key for asset in all_assets]

    # 5 dbt models
    assert len(all_assets) == 2
    assert len(all_assets_keys) == 2

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customers"]
    first_asset_kinds = next(spec.kinds for spec in sorted(all_assets))
    assert "dbtcloud" in first_asset_kinds
    assert "dbt" not in first_asset_kinds


def test_load_check_specs(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_checks = load_dbt_cloud_check_specs(workspace=workspace)
    all_checks_keys = [check.key for check in all_checks]

    # 20 dbt tests
    assert len(all_checks) == 20
    assert len(all_checks_keys) == 20

    # Sanity check outputs
    first_check_key = next(key for key in sorted(all_checks_keys))
    assert first_check_key.name == "not_null_customers_customer_id"
    assert first_check_key.asset_key.path == ["customers"]


def test_load_check_specs_select(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_checks = load_dbt_cloud_check_specs(workspace=workspace, select="raw_customers+")
    all_checks_keys = [check.key for check in all_checks]

    # 4 dbt tests
    assert len(all_checks) == 4
    assert len(all_checks_keys) == 4

    # Sanity check outputs
    first_check_key = next(key for key in sorted(all_checks_keys))
    assert first_check_key.name == "not_null_customers_customer_id"
    assert first_check_key.asset_key.path == ["customers"]


def test_load_check_specs_exclude(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_checks = load_dbt_cloud_check_specs(workspace=workspace, exclude="raw_customers+")
    all_checks_keys = [check.key for check in all_checks]

    # 15 dbt tests
    assert len(all_checks) == 15
    assert len(all_checks_keys) == 15

    # Sanity check outputs
    first_check_key = next(key for key in sorted(all_checks_keys))
    assert (
        first_check_key.name
        == "accepted_values_orders_status__placed__shipped__completed__return_pending__returned"
    )
    assert first_check_key.asset_key.path == ["orders"]


def test_load_check_specs_selector(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    all_checks = load_dbt_cloud_check_specs(
        workspace=workspace, selector="raw_customer_child_models"
    )
    all_checks_keys = [check.key for check in all_checks]

    # 4 dbt tests
    assert len(all_checks) == 4
    assert len(all_checks_keys) == 4

    # Sanity check outputs
    first_check_key = next(key for key in sorted(all_checks_keys))
    assert first_check_key.name == "not_null_customers_customer_id"
    assert first_check_key.asset_key.path == ["customers"]
