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
        assert len(actual_workspace_data.views_by_id) == 1
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

        # 1 view and 1 data source
        assert len(all_assets) == 2

        # Sanity check outputs, translator tests cover details here
        view_asset = next(asset for asset in all_assets if "workbook" in asset.key.path[0])
        assert view_asset.key.path == ["test_workbook", "view", "sales"]

        data_source_asset = next(asset for asset in all_assets if "datasource" in asset.key.path[0])
        assert data_source_asset.key.path == ["superstore_datasource"]
