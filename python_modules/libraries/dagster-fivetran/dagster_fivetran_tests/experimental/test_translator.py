import uuid
from typing import Callable

from dagster_fivetran import FivetranWorkspace


def test_fivetran_workspace_data_to_fivetran_connector_table_props_data(
    fetch_workspace_data_api_mocks: Callable,
) -> None:
    api_key = uuid.uuid4().hex
    api_secret = uuid.uuid4().hex

    resource = FivetranWorkspace(api_key=api_key, api_secret=api_secret)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 4
    assert (
        table_props_data[0].table == "schema_name_in_destination_1.table_name_in_destination_1"
    )
    assert (
        table_props_data[1].table == "schema_name_in_destination_1.table_name_in_destination_2"
    )
    assert (
        table_props_data[2].table == "schema_name_in_destination_2.table_name_in_destination_1"
    )
    assert (
        table_props_data[3].table == "schema_name_in_destination_2.table_name_in_destination_2"
    )
