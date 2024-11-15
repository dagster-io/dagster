import responses
from dagster._vendored.dateutil import parser
from dagster_fivetran import FivetranWorkspace
from dagster_fivetran.translator import MIN_TIME_STR

from dagster_fivetran_tests.experimental.conftest import (
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
)


def test_basic_resource_request(
    connector_id: str,
    destination_id: str,
    group_id: str,
    all_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    client = resource.get_client()
    client.get_connectors_for_group(group_id=group_id)
    client.get_destination_details(destination_id=destination_id)
    client.get_groups()
    client.get_schema_config_for_connector(connector_id=connector_id)

    assert len(all_api_mocks.calls) == 4
    assert "Basic" in all_api_mocks.calls[0].request.headers["Authorization"]
    assert group_id in all_api_mocks.calls[0].request.url
    assert destination_id in all_api_mocks.calls[1].request.url
    assert "groups" in all_api_mocks.calls[2].request.url
    assert f"{connector_id}/schemas" in all_api_mocks.calls[3].request.url

    # reset calls
    all_api_mocks.calls.reset()
    client.get_connector_details(connector_id=connector_id)
    client.update_schedule_type_for_connector(connector_id=connector_id, schedule_type="auto")

    assert len(all_api_mocks.calls) == 2
    assert connector_id in all_api_mocks.calls[0].request.url
    assert connector_id in all_api_mocks.calls[1].request.url
    assert all_api_mocks.calls[1].request.method == "PATCH"

    all_api_mocks.calls.reset()
    client.start_sync(connector_id=connector_id)
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/force" in all_api_mocks.calls[2].request.url

    all_api_mocks.calls.reset()
    client.start_resync(connector_id=connector_id, resync_parameters=None)
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/resync" in all_api_mocks.calls[2].request.url

    all_api_mocks.calls.reset()
    client.start_resync(connector_id=connector_id, resync_parameters={"property1": ["string"]})
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/schemas/tables/resync" in all_api_mocks.calls[2].request.url

    all_api_mocks.calls.reset()
    client.poll_sync(
        connector_id=connector_id, previous_sync_completed_at=parser.parse(MIN_TIME_STR)
    )
    assert len(all_api_mocks.calls) == 2
