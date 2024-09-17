# ruff: noqa: SLF001

import uuid
from typing import Callable, Type, Union

import pytest
import responses
from dagster import asset, instance_for_test, materialize
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
@pytest.mark.usefixtures("api_token")
@pytest.mark.usefixtures("workbook_id")
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_basic_resource_request(
    clazz: Union[Type[TableauCloudWorkspace], Type[TableauServerWorkspace]],
    host_key: str,
    host_value: str,
    site_name: str,
    api_token: str,
    workbook_id: str,
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

    # Must initialize the resource's client before passing it to the mock responses
    resource.build_client()

    with workspace_data_api_mocks_fn(client=resource._client) as response:
        # Remove the resource's client to properly test the resource
        resource._client = None

        @asset
        def test_assets():
            with resource.get_client() as client:
                client.get_workbooks()
                client.get_workbook(workbook_id=workbook_id)

        with instance_for_test() as instance:
            materialize(
                [test_assets],
                instance=instance,
                resources={"tableau": resource},
            )

        assert len(response.calls) == 4
        assert "X-tableau-auth" not in response.calls[0].request.headers
        assert response.calls[1].request.headers["X-tableau-auth"] == api_token
        assert response.calls[2].request.headers["X-tableau-auth"] == api_token
