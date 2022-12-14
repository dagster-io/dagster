from assets_pandas_pyspark.assets import spark_asset, table_assets

from dagster import load_assets_from_modules, materialize
from dagster._core.test_utils import instance_for_test


def test_weather_assets():
    from assets_pandas_pyspark.local_filesystem_io_manager import local_filesystem_io_manager

    with instance_for_test() as instance:
        assert materialize(
            load_assets_from_modules([table_assets]),
            instance=instance,
            resources={"io_manager": local_filesystem_io_manager},
        ).success


def test_spark_weather_assets():
    from assets_pandas_pyspark.local_spark_filesystem_io_manager import local_filesystem_io_manager

    with instance_for_test() as instance:
        assert materialize(
            load_assets_from_modules([table_assets, spark_asset]),
            instance=instance,
            resources={"io_manager": local_filesystem_io_manager},
        ).success
