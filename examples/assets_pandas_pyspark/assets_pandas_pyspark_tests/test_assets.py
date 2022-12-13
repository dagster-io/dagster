from assets_pandas_pyspark.assets import spark_asset, table_assets

from dagster import load_assets_from_modules, materialize, with_resources
from dagster._core.test_utils import instance_for_test


def test_weather_assets():
    from assets_pandas_pyspark.local_filesystem_io_manager import local_filesystem_io_manager

    weather_assets = with_resources(
        load_assets_from_modules([table_assets]),
        resource_defs={"io_manager": local_filesystem_io_manager},
    )
    with instance_for_test() as instance:
        assert materialize(weather_assets, instance=instance).success


def test_spark_weather_assets():
    from assets_pandas_pyspark.local_spark_filesystem_io_manager import local_filesystem_io_manager

    spark_weather_assets = with_resources(
        load_assets_from_modules([table_assets, spark_asset]),
        resource_defs={"io_manager": local_filesystem_io_manager},
    )

    with instance_for_test() as instance:
        assert materialize(spark_weather_assets, instance=instance).success
