import dagster as dg


def process_data_for_partition(partition_date):
    """Example function to process data for a specific partition."""
    # Your actual data processing logic would go here
    return f"Processed data for {partition_date}"


class MyPartitionedComponent:
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset
        def my_partitioned_asset(context: dg.AssetExecutionContext):
            # Access the current partition key
            partition_key = context.partition_key

            # Use partition key to filter data or modify execution logic
            # For example, if using a time-based partition:
            partition_date = context.partition_time_window.start

            # Your execution logic here, using the partition information
            return process_data_for_partition(partition_date)

        # Apply partitions and return definitions
        return dg.Definitions(
            assets=[
                my_partitioned_asset.with_attributes(
                    partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01")
                )
            ]
        )
