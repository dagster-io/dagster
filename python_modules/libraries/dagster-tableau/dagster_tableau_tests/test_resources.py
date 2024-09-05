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

    fake_personal_access_token_name = "fake_personal_access_token_name"
    fake_personal_access_token_value = uuid.uuid4().hex
    fake_site_name = "fake_site_name"
    fake_site_id = uuid.uuid4().hex
    fake_api_token = uuid.uuid4().hex

    resource_args = {
        "personal_access_token_name": fake_personal_access_token_name,
        "personal_access_token_value": fake_personal_access_token_value,
        "site_name": fake_site_name,
        host_key: fake_host_value,
    }

    resource = clazz(**resource_args)

    responses.add(
        method=responses.POST,
        url=f"{resource.api_base_url}/auth/signin",
        json={"credentials": {"site": {"id": fake_site_id}, "token": fake_api_token}},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=f"{resource.api_base_url}/sites/{fake_site_id}/workbooks",
        json={},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=f"{resource.api_base_url}/auth/signout",
        json={},
        status=200,
    )

    @asset
    def test_assets(tableau: clazz):
        tableau.get_workbooks()

    with instance_for_test() as instance:
        materialize(
            [test_assets],
            instance=instance,
            resources={"tableau": resource},
        )

    assert len(responses.calls) == 3
    assert "X-tableau-auth" not in responses.calls[0].request.headers
    assert responses.calls[1].request.headers["X-tableau-auth"] == fake_api_token
    assert responses.calls[2].request.headers["X-tableau-auth"] == fake_api_token
