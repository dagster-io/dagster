from assets_pandas_pyspark.assets import spark_asset, table_assets
from dagster import materialize
from dagster._core.test_utils import instance_for_test


def test_weather_assets():
    from assets_pandas_pyspark.local_filesystem_io_manager import LocalFileSystemIOManager

    with instance_for_test() as instance:
        assert materialize(
            list(table_assets.defs.assets or []),  # ty: ignore[invalid-argument-type]
            instance=instance,
            resources={"io_manager": LocalFileSystemIOManager()},
        ).success


def test_spark_weather_assets():
    from assets_pandas_pyspark.local_spark_filesystem_io_manager import LocalFileSystemIOManager

    assets = list(table_assets.defs.assets or [])
    with instance_for_test() as instance:
        assert materialize(
            [*list(assets), spark_asset.daily_temperature_high_diffs],  # ty: ignore[invalid-argument-type]
            instance=instance,
            resources={"io_manager": LocalFileSystemIOManager()},
        ).success
