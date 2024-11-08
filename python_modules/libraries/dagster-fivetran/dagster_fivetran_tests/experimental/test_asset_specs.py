import uuid

import responses
from dagster_fivetran import FivetranWorkspace


def test_fetch_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    api_key = uuid.uuid4().hex
    api_secret = uuid.uuid4().hex

    resource = FivetranWorkspace(api_key=api_key, api_secret=api_secret)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1
