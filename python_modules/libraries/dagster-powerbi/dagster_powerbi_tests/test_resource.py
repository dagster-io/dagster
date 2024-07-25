import uuid

import responses
from dagster_powerbi import PowerBIResource
from dagster_powerbi.resource import BASE_API_URL


@responses.activate
def test_basic_resource_request() -> None:
    fake_token = uuid.uuid4().hex
    fake_workspace_id = uuid.uuid4().hex
    resource = PowerBIResource(
        api_token=fake_token,
        workspace_id=fake_workspace_id,
    )

    responses.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{fake_workspace_id}/reports",
        json={},
        status=200,
    )

    resource.get_reports()

    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == f"Bearer {fake_token}"
