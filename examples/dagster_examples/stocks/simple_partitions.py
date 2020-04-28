from dagster import Partition, PartitionSetDefinition


def get_stock_ticker_partitions():
    return [
        Partition("AAPL"),
        Partition("GOOG"),
        Partition("MSFT"),
        Partition("TSLA"),
    ]


def environment_dict_for_ticker_partition(partition):
    ticker_symbol = partition.value

    return {'solids': {'query_historical_stock_data': {'config': {'symbol': ticker_symbol}}}}


stock_ticker_partition_sets = PartitionSetDefinition(
    name="stock_ticker_partition_sets",
    pipeline_name="compute_total_stock_volume",
    partition_fn=get_stock_ticker_partitions,
    environment_dict_fn_for_partition=environment_dict_for_ticker_partition,
)


def define_partitions():
    return [stock_ticker_partition_sets]
