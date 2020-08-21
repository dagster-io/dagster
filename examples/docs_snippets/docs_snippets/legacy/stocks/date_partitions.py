import datetime

from dateutil.relativedelta import relativedelta

from dagster import Partition, PartitionSetDefinition
from dagster.utils.partitions import date_partition_range


def stock_data_partitions():
    return [
        Partition(datetime.datetime(2019, 1, 1)),
        Partition(datetime.datetime(2019, 2, 1)),
        Partition(datetime.datetime(2019, 3, 1)),
        Partition(datetime.datetime(2019, 4, 1)),
    ]


def run_config_fn_for_date(partition):
    date = partition.value

    previous_month_last_day = date - datetime.timedelta(days=1)
    previous_month_first_day = previous_month_last_day.replace(day=1)

    return {
        "solids": {
            "query_historical_stock_data": {
                "config": {
                    "ds_start": previous_month_first_day.strftime("%Y-%m-%d"),
                    "ds_end": previous_month_last_day.strftime("%Y-%m-%d"),
                    "symbol": "AAPL",
                }
            }
        }
    }


stock_data_partitions_set = PartitionSetDefinition(
    name="stock_data_partitions_set",
    pipeline_name="compute_total_stock_volume",
    partition_fn=date_partition_range(
        start=datetime.datetime(2018, 1, 1),
        end=datetime.datetime(2019, 1, 1),
        delta=relativedelta(months=1),
    ),
    run_config_fn_for_partition=run_config_fn_for_date,
)


def define_partitions():
    return [stock_data_partitions_set]
