import uuid
from typing import Callable

from dagster_fivetran import FivetranWorkspace


def test_basic_resource_request(
    connector_id: str, destination_id: str, group_id: str, workspace_data_api_mocks_fn: Callable
) -> None:
    api_key = uuid.uuid4().hex
    api_secret = uuid.uuid4().hex

    resource = FivetranWorkspace(api_key=api_key, api_secret=api_secret)

    with workspace_data_api_mocks_fn() as response:
        client = resource.get_client()
        client.get_connector_details(connector_id=connector_id)
        client.get_connectors_for_group(group_id=group_id)
        client.get_destination_details(destination_id=destination_id)
        client.get_groups()

        assert len(response.calls) == 4

        assert "Basic" in response.calls[0].request.headers["Authorization"]
        assert connector_id in response.calls[0].request.url
        assert group_id in response.calls[1].request.url
        assert destination_id in response.calls[2].request.url
        assert "groups" in response.calls[3].request.url
