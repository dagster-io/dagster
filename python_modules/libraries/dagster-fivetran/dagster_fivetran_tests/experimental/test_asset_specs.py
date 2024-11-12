import responses
from dagster_fivetran import FivetranWorkspace

from dagster_fivetran_tests.experimental.conftest import TEST_API_KEY, TEST_API_SECRET


def test_fetch_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1
