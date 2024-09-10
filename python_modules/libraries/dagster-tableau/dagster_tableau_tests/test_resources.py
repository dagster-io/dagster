# ruff: noqa: SLF001

import uuid

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
@pytest.mark.usefixtures("workspace_data_api_mocks_fn")
def test_basic_resource_request(
    clazz, host_key, host_value, site_name, api_token, workspace_data_api_mocks_fn
) -> None:

    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"
    fake_site_id = uuid.uuid4().hex
    fake_api_token = uuid.uuid4().hex
    fake_workbook_id = uuid.uuid4().hex

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)

    # Must initialize the resource's client before passing it to the mock responses
    resource.build_client()

    yield from workspace_data_api_mocks_fn(api_base_url=resource.api_base_url)

    responses.add(
        method=responses.POST,
        url=f"{resource._client.rest_api_base_url}/auth/signin",
        json={"credentials": {"site": {"id": fake_site_id}, "token": fake_api_token}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{resource._client.rest_api_base_url}/sites/{fake_site_id}/workbooks",
        json={},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{resource._client.metadata_api_base_url}",
        json={
            "query": resource._client.workbook_graphql_query,
            "variables": {"luid": fake_workbook_id},
        },
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{resource._client.rest_api_base_url}/auth/signout",
        json={},
        status=200,
    )

    # Remove the resource's client to properly test the resource
    resource._client = None

    @asset
    def test_assets():
        with resource.get_client() as client:
            client.get_workbooks()
            client.get_workbook(workbook_id=fake_workbook_id)

    with instance_for_test() as instance:
        materialize(
            [test_assets],
            instance=instance,
            resources={"tableau": resource},
        )

    assert len(responses.calls) == 4
    assert "X-tableau-auth" not in responses.calls[0].request.headers
    assert responses.calls[1].request.headers["X-tableau-auth"] == api_token
    assert responses.calls[2].request.headers["X-tableau-auth"] == api_token
