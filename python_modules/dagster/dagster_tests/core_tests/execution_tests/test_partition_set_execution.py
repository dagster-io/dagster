import dagster as dg
from dagster._core.storage.tags import ASSET_PARTITIONS_TAG


def test_asset_backfill_partition_set() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])

    @dg.asset(partitions_def=partitions_def)
    def my_partitioned_asset(context: dg.AssetExecutionContext) -> None:
        assert set(context.partition_keys) == {"b", "d"}

    result = dg.materialize(
        assets=[my_partitioned_asset],
        tags={
            ASSET_PARTITIONS_TAG: "b,d",
        },
    )
    assert result.success
