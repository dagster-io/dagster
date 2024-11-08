import uuid

import responses
from dagster_fivetran import FivetranWorkspace


def test_basic_resource_request(
    connector_id: str,
    destination_id: str,
    group_id: str,
    workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    api_key = uuid.uuid4().hex
    api_secret = uuid.uuid4().hex

    resource = FivetranWorkspace(api_key=api_key, api_secret=api_secret)

    client = resource.get_client()
    client.get_connector_details(connector_id=connector_id)
    client.get_connectors_for_group(group_id=group_id)
    client.get_destination_details(destination_id=destination_id)
    client.get_groups()

    assert len(workspace_data_api_mocks.calls) == 4

    assert "Basic" in workspace_data_api_mocks.calls[0].request.headers["Authorization"]
    assert connector_id in workspace_data_api_mocks.calls[0].request.url
    assert group_id in workspace_data_api_mocks.calls[1].request.url
    assert destination_id in workspace_data_api_mocks.calls[2].request.url
    assert "groups" in workspace_data_api_mocks.calls[3].request.url
