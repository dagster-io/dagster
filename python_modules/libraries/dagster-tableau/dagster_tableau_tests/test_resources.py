# ruff: noqa: SLF001

import uuid

import pytest
import responses
from dagster import asset, instance_for_test, materialize
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace


@responses.activate
@pytest.mark.parametrize(
    "args",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_basic_resource_request(args) -> None:
    clazz = args[0]
    host_key = args[1]
    fake_host_value = args[2]

    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"
    fake_site_name = "fake_site_name"
    fake_site_id = uuid.uuid4().hex
    fake_api_token = uuid.uuid4().hex
    fake_workbook_id = uuid.uuid4().hex

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": fake_site_name,
        host_key: fake_host_value,
    }

    resource = clazz(**resource_args)
    resource.build_client()

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

    @asset
    def test_assets(tableau: clazz):
        with tableau.get_client() as client:
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
    assert responses.calls[1].request.headers["X-tableau-auth"] == fake_api_token
    assert responses.calls[2].request.headers["X-tableau-auth"] == fake_api_token
