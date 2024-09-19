import os
import tempfile
from unittest import mock

from dagster import RunRequest, SensorResult, build_sensor_context, materialize
from dagster._core.test_utils import instance_for_test
from docs_snippets.concepts.partitions_schedules_sensors.dynamic_partitioned_asset import (
    image_sensor,
    images,
)

DIR = "images"


def test():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        partition_key = "strawberry"
        os.mkdir(os.path.join(tmpdir_path, DIR))
        open(os.path.join(tmpdir_path, DIR, partition_key), "a").close()

        mockenv = mock.patch.dict(
            os.environ, {"MY_DIRECTORY": os.path.join(os.path.join(tmpdir_path, DIR))}
        )
        try:
            mockenv.start()
            with instance_for_test() as instance:
                with build_sensor_context(instance=instance) as context:
                    result = image_sensor(context)
                    assert isinstance(result, SensorResult)
                    assert len(result.run_requests) == 1
                    assert result.run_requests[0].partition_key == partition_key
                    assert len(result.dynamic_partitions_requests) == 1
                    assert result.dynamic_partitions_requests[0].partition_keys == [
                        partition_key
                    ]

        finally:
            mockenv.stop()
