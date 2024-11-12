import responses
from dagster_fivetran import FivetranWorkspace

from dagster_fivetran_tests.experimental.conftest import TEST_API_KEY, TEST_API_SECRET


def test_basic_resource_request(
    connector_id: str,
    destination_id: str,
    group_id: str,
    all_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)

    client = resource.get_client()
    client.get_connector_details(connector_id=connector_id)
    client.get_connectors_for_group(group_id=group_id)
    client.get_destination_details(destination_id=destination_id)
    client.get_groups()
    client.get_schema_config_for_connector(connector_id=connector_id)

    assert len(all_api_mocks.calls) == 5

    assert "Basic" in all_api_mocks.calls[0].request.headers["Authorization"]
    assert connector_id in all_api_mocks.calls[0].request.url
    assert group_id in all_api_mocks.calls[1].request.url
    assert destination_id in all_api_mocks.calls[2].request.url
    assert "groups" in all_api_mocks.calls[3].request.url
    assert f"{connector_id}/schemas" in all_api_mocks.calls[4].request.url
