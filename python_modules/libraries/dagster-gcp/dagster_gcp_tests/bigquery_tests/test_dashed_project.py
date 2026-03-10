import pytest
from unittest import mock
from dagster_gcp.bigquery.resources import fetch_last_updated_timestamps
from google.cloud import bigquery


def test_fetch_last_updated_timestamps_dashed_project():
    client = mock.Mock(spec=bigquery.Client)
    dataset_id = "my-dashed-project.my_dataset"
    table_ids = ["my_table"]

    # Mock the return value of client.query().result()
    mock_row = mock.Mock()
    mock_row.table_id = "my_table"
    mock_row.last_modified_time = 123456789
    client.query.return_value.result.return_value = [mock_row]

    fetch_last_updated_timestamps(client=client, dataset_id=dataset_id, table_ids=table_ids)

    # Verify the query string has backticks
    args, kwargs = client.query.call_args
    query_str = args[0]
    assert f"`{dataset_id}`.__TABLES__" in query_str
