from typing import Callable

from dagster_fivetran import FivetranWorkspace

from dagster_fivetran_tests.experimental.conftest import TEST_API_KEY, TEST_API_SECRET


def test_fivetran_workspace_data_to_fivetran_connector_table_props_data(
    fetch_workspace_data_api_mocks: Callable,
) -> None:
    resource = FivetranWorkspace(api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 4
    assert table_props_data[0].table == "schema_name_in_destination_1.table_name_in_destination_1"
    assert table_props_data[1].table == "schema_name_in_destination_1.table_name_in_destination_2"
    assert table_props_data[2].table == "schema_name_in_destination_2.table_name_in_destination_1"
    assert table_props_data[3].table == "schema_name_in_destination_2.table_name_in_destination_2"
