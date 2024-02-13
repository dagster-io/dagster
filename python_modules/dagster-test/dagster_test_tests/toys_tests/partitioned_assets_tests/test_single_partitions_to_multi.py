import tempfile

from dagster import DagsterInstance, MultiPartitionKey, materialize
from dagster_test.toys.partitioned_assets.single_partitions_to_multi import (
    multi_partitions,
    single_partitions,
)


def test_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral(tempdir=tmpdir_path)

        assert materialize([single_partitions], instance=instance, partition_key="a").success
        assert materialize(
            [single_partitions.to_source_asset(), multi_partitions],
            instance=instance,
            partition_key=MultiPartitionKey({"abc": "a", "123": "1"}),
        ).success
