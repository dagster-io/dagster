import uuid

import pytest
import responses
from dagster_tableau import TableauCloudWorkspace, TableauServerWorkspace

from dagster_tableau_tests.conftest import SAMPLE_CONNECTIONS, SAMPLE_WORKBOOK


@responses.activate
@pytest.mark.parametrize(
    "clazz,host_key,fake_host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data(clazz, host_key, fake_host_value) -> None:
    fake_personal_access_token_name = "fake_personal_access_token_name"
    fake_personal_access_token_value = uuid.uuid4().hex
    fake_site_name = "fake_site_name"

    resource_args = {
        "personal_access_token_name": fake_personal_access_token_name,
        "personal_access_token_value": fake_personal_access_token_value,
        "site_name": fake_site_name,
        host_key: fake_host_value,
    }

    resource = clazz(**resource_args)

    # TODO fix after updating the resource
    fake_site_id = "fake_site_id"
    fake_api_token = "fake_api_token"
    resource._site_id = fake_site_id  # noqa
    resource._api_token = fake_api_token  # noqa

    # TODO move to conftest as a fixture
    responses.add(
        method=responses.GET,
        url=f"{resource.api_base_url}/sites/{fake_site_id}/workbooks",
        json={"workbooks": {"workbook": [{**SAMPLE_WORKBOOK}]}},
        status=200,
    )

    responses.add(
        method=responses.GET,
        url=f"{resource.api_base_url}/sites/{fake_site_id}/workbooks/b75fc023-a7ca-4115-857b-4342028640d0",
        json={"workbook": {**SAMPLE_WORKBOOK}},
        status=200,
    )

    responses.add(
        method=responses.GET,
        url=f"{resource.api_base_url}/sites/{fake_site_id}/workbooks/b75fc023-a7ca-4115-857b-4342028640d0/connections",
        json=SAMPLE_CONNECTIONS,
        status=200,
    )

    actual_workspace_data = resource.fetch_tableau_workspace_data()
    assert len(actual_workspace_data.workbooks_by_id) == 1
    assert len(actual_workspace_data.views_by_id) == 1
    assert len(actual_workspace_data.data_sources_by_id) == 1
