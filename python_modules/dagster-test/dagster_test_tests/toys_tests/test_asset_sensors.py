from dagster import build_multi_asset_sensor_context, instance_for_test, materialize
from dagster_test.toys.asset_sensors import (
    partitioned_assets,
    partitioned_multi_asset_sensor,
)
from dagster_test.toys.repo import assets_with_sensors_repository

partitioned_asset = partitioned_assets[0]


def test_partitioned_multi_asset_sensor():
    with instance_for_test() as instance:
        with build_multi_asset_sensor_context(
            repository_def=assets_with_sensors_repository,
            instance=instance,
            monitored_assets=[partitioned_asset.key for partitioned_asset in partitioned_assets],
        ) as context:
            materialize([partitioned_asset], partition_key="1", instance=instance)

            result = partitioned_multi_asset_sensor(context)
            assert len(result) == 1
