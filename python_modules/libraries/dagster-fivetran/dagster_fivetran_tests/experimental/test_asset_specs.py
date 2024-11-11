import responses
from dagster_fivetran import FivetranWorkspace


def test_fetch_fivetran_workspace_data(
    api_key: str,
    api_secret: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(api_key=api_key, api_secret=api_secret)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1
