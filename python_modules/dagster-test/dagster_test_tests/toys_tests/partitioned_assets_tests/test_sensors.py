from dagster import build_sensor_context
from dagster._core.test_utils import instance_for_test
from dagster_test.toys.partitioned_assets.partitioned_run_request_sensors import (
    ints_dynamic_partitions_asset_selection_sensor,
    ints_dynamic_partitions_job_sensor,
    upstream_daily_partitioned_asset_sensor,
)
from dagster_test.toys.repo import partitioned_assets_repository


def test_ints_sensors():
    ints_sensors = [
        ints_dynamic_partitions_asset_selection_sensor,
        ints_dynamic_partitions_job_sensor,
    ]
    with instance_for_test() as instance:
        with build_sensor_context(
            instance=instance,
            repository_def=partitioned_assets_repository,
        ) as context:
            for ints_sensor in ints_sensors:
                result = ints_sensor(context)
                assert len(result.run_requests) == 1
                assert len(result.dynamic_partitions_requests) == 1


def test_daily_partitioned_sensor():
    with build_sensor_context(
        repository_def=partitioned_assets_repository,
    ) as context:
        result = upstream_daily_partitioned_asset_sensor.evaluate_tick(context)
        assert len(result.run_requests) == 2
