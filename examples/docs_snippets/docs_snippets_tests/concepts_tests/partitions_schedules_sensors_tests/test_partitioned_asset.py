from unittest.mock import patch

from dagster import materialize_to_memory
from docs_snippets.concepts.partitions_schedules_sensors.partitioned_asset import (
    my_daily_partitioned_asset,
)


@patch("urllib.request.urlretrieve")
def test_partitioned_asset(mock_urlretrieve):
    assert materialize_to_memory(
        [my_daily_partitioned_asset], partition_key="2022-01-01"
    ).success
    assert mock_urlretrieve.call_args[0] == (
        "coolweatherwebsite.com/weather_obs&date=2022-01-01",
        "weather_observations/2022-01-01.csv",
    )
