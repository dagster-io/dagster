# ruff: noqa: SLF001

import uuid
from typing import Callable, Type, Union

import pytest
import responses
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_fetch_tableau_workspace_data(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workspace_data_api_mocks_fn: Callable,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore
    resource.build_client()

    with workspace_data_api_mocks_fn(client=resource._client):
        actual_workspace_data = resource.fetch_tableau_workspace_data()
        assert len(actual_workspace_data.workbooks_by_id) == 1
        assert len(actual_workspace_data.sheets_by_id) == 1
        assert len(actual_workspace_data.dashboards_by_id) == 1
        assert len(actual_workspace_data.data_sources_by_id) == 1


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.usefixtures("site_name")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_translator_spec(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    workspace_data_api_mocks_fn: Callable,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)  # type: ignore
    resource.build_client()

    with workspace_data_api_mocks_fn(client=resource._client):
        all_assets = resource.build_defs().get_asset_graph().assets_defs
        all_assets_keys = [key for asset in all_assets for key in asset.keys]

        # 1 multi-asset for tableau assets (sheets and dashboards) and 1 data source external asset
        assert len(all_assets) == 2
        # 1 sheet, 1 dashboard and 1 data source
        assert len(all_assets_keys) == 3

        # Sanity check outputs, translator tests cover details here
        sheet_asset_key = next(
            key for key in all_assets_keys if "workbook" in key.path[0] and "sheet" in key.path[1]
        )
        assert sheet_asset_key.path == ["test_workbook", "sheet", "sales"]

        dashboard_asset_key = next(
            key
            for key in all_assets_keys
            if "workbook" in key.path[0] and "dashboard" in key.path[1]
        )
        assert dashboard_asset_key.path == ["test_workbook", "dashboard", "dashboard_sales"]

        data_source_asset_key = next(key for key in all_assets_keys if "datasource" in key.path[0])
        assert data_source_asset_key.path == ["superstore_datasource"]
