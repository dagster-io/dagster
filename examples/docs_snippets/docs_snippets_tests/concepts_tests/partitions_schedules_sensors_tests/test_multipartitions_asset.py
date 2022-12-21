from dagster import MultiPartitionKey, materialize
from docs_snippets.concepts.partitions_schedules_sensors.multipartitions_asset import (
    multi_partitions_asset,
)


def test():
    result = materialize(
        [multi_partitions_asset],
        partition_key=MultiPartitionKey({"date": "2022-01-01", "color": "red"}),
    )
    assert result.success
    assert (
        result.asset_materializations_for_node("multi_partitions_asset")[0].partition
        == "red|2022-01-01"
    )
