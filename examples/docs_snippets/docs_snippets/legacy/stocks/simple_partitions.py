from dagster import Partition, PartitionSetDefinition


def get_stock_ticker_partitions():
    return [
        Partition("AAPL"),
        Partition("GOOG"),
        Partition("MSFT"),
        Partition("TSLA"),
    ]


def run_config_for_ticker_partition(partition):
    ticker_symbol = partition.value

    return {"solids": {"query_historical_stock_data": {"config": {"symbol": ticker_symbol}}}}


stock_ticker_partition_sets = PartitionSetDefinition(
    name="stock_ticker_partition_sets",
    pipeline_name="compute_total_stock_volume",
    partition_fn=get_stock_ticker_partitions,
    run_config_fn_for_partition=run_config_for_ticker_partition,
)


def define_partitions():
    return [stock_ticker_partition_sets]
