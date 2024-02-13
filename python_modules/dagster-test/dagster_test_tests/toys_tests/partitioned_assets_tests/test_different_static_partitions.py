import tempfile

from dagster import DagsterInstance, materialize
from dagster_test.toys.partitioned_assets.different_static_partitions import (
    static_partitioned_asset1,
    static_partitioned_asset2,
)


def test_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral(tempdir=tmpdir_path)

        assert materialize(
            [static_partitioned_asset1], instance=instance, partition_key="a"
        ).success
        assert materialize(
            [static_partitioned_asset1.to_source_asset(), static_partitioned_asset2],
            instance=instance,
            partition_key="1",
        ).success
