# start_multi_partitions_marker
from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2022-01-01"),
            "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
        }
    )
)
def multi_partitions_asset(context: AssetExecutionContext):
    context.log.info(context.partition_key.keys_by_dimension)


# end_multi_partitions_marker

# start_multi_partitions_key_marker

from dagster import MultiPartitionKey, materialize

result = materialize(
    [multi_partitions_asset],
    partition_key=MultiPartitionKey({"date": "2022-01-01", "color": "red"}),
)

# end_multi_partitions_key_marker
