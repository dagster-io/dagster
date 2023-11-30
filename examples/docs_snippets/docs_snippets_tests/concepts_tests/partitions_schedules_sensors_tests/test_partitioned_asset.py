from unittest.mock import patch

from dagster import materialize_to_memory
from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset import (
    my_daily_partitioned_asset,
)


@patch("urllib.request.urlretrieve")
def test_partitioned_asset(mock_urlretrieve):
    assert materialize_to_memory(
        [my_daily_partitioned_asset], partition_key="2023-10-01"
    ).success
    assert mock_urlretrieve.call_args[0] == (
        "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date=2023-10-01",
        "nasa/2023-10-01.csv",
    )
