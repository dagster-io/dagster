import tempfile

from dagster import DagsterInstance, materialize
from dagster_test.toys.partitioned_assets.hourly_partitions_to_daily import (
    daily_asset,
    hourly_asset1,
    hourly_asset2,
)


def test_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.ephemeral(tempdir=tmpdir_path)

        assert materialize(
            [hourly_asset1, hourly_asset2], instance=instance, partition_key="2023-02-01-00:00"
        ).success
        assert materialize(
            [hourly_asset1.to_source_asset(), hourly_asset2.to_source_asset(), daily_asset],
            instance=instance,
            partition_key="2023-02-01",
        ).success
