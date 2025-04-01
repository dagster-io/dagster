# start_multi_partitions_marker
import dagster as dg


@dg.asset(
    partitions_def=dg.MultiPartitionsDefinition(
        {
            "date": dg.DailyPartitionsDefinition(start_date="2022-01-01"),
            "color": dg.StaticPartitionsDefinition(["red", "yellow", "blue"]),
        }
    )
)
def multi_partitions_asset(context: dg.AssetExecutionContext):
    if isinstance(context.partition_key, MultiPartitionKey):
        context.log.info(context.partition_key.keys_by_dimension)


# end_multi_partitions_marker

# start_multi_partitions_key_marker

from dagster import MultiPartitionKey, materialize

result = materialize(
    [multi_partitions_asset],
    partition_key=MultiPartitionKey({"date": "2022-01-01", "color": "red"}),
)

# end_multi_partitions_key_marker
