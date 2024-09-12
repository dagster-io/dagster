from dagster import materialize
from dagster._core.test_utils import instance_for_test

from assets_pandas_pyspark.assets import spark_asset, table_assets


def test_weather_assets():
    from assets_pandas_pyspark.local_filesystem_io_manager import LocalFileSystemIOManager

    with instance_for_test() as instance:
        assert materialize(
            table_assets.defs.assets,
            instance=instance,
            resources={"io_manager": LocalFileSystemIOManager()},
        ).success


def test_spark_weather_assets():
    from assets_pandas_pyspark.local_spark_filesystem_io_manager import LocalFileSystemIOManager

    with instance_for_test() as instance:
        assert materialize(
            [*table_assets.defs.assets, spark_asset.daily_temperature_high_diffs],
            instance=instance,
            resources={"io_manager": LocalFileSystemIOManager()},
        ).success
