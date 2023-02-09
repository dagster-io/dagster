import os
import tempfile
from unittest import mock

from dagster import MultiPartitionKey, RunRequest, build_sensor_context, materialize
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
        mockenv.start()
        with instance_for_test() as instance:
            with build_sensor_context(instance=instance) as context:
                result = list(image_sensor(context))
                assert len(result) == 1
                assert isinstance(result[0], RunRequest)
                assert result[0].partition_key == partition_key

            assert instance.has_dynamic_partition("images", partition_key)

            result = materialize(
                [images], instance=instance, partition_key=partition_key
            )
            assert result.success
            assert (
                result.asset_materializations_for_node("images")[0].partition
                == partition_key
            )
        mockenv.stop()
