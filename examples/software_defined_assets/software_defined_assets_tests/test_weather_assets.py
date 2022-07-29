from software_defined_assets.weather_assets import weather_assets

from dagster import materialize
from dagster._core.test_utils import instance_for_test


def test_airport_weather_assets():
    with instance_for_test() as instance:
        assert materialize(weather_assets, instance=instance).success
