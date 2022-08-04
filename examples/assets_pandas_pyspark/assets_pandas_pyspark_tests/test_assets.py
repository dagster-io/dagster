from assets_pandas_pyspark.assets.spark_weather_assets import spark_weather_assets
from assets_pandas_pyspark.assets.weather_assets import weather_assets

from dagster import materialize
from dagster._core.test_utils import instance_for_test


def test_weather_assets():
    with instance_for_test() as instance:
        assert materialize(weather_assets, instance=instance).success


def test_spark_weather_assets():
    with instance_for_test() as instance:
        assert materialize(spark_weather_assets, instance=instance).success
