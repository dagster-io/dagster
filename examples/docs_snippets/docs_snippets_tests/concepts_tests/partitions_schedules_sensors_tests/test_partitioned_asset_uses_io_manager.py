from unittest.mock import MagicMock, patch

from pandas import DataFrame

from dagster import materialize_to_memory
from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset_uses_io_manager import (
    my_daily_partitioned_asset,
)


@patch(
    "docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset_uses_io_manager.pd.read_csv"
)
def test_partitioned_asset(mock_read_csv):
    mock_read_csv.return_value = MagicMock(spec=DataFrame)
    assert materialize_to_memory(
        [my_daily_partitioned_asset], partition_key="2022-01-01"
    ).success
