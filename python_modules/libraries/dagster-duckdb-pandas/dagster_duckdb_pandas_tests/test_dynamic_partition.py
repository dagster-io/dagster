import ast
import base64
import json
import os

from dagster import (
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
    StaticPartitionsDefinition,
    SkipReason,
    asset,
    define_asset_job,
    sensor,
    instance_for_test,
    materialize
)
from dagster_duckdb_pandas import duckdb_pandas_io_manager

import pandas as pd




# --- Assets
dynamic_regions = DynamicPartitionsDefinition(name="dynamic_regions")
#dynamic_regions = StaticPartitionsDefinition(["northeast","southwest","northeast_oopsie"])

@asset(
    partitions_def=dynamic_regions,
    key_prefix=["vehicles"],
)
def plant_data(context) -> pd.DataFrame:
    """
    Raw data is read from directory, with each new file
    creating a new partition

    """

    file = f"{context.asset_partition_key_for_output()}.csv"
    data = pd.read_csv(f"/Users/jamie/dev/dagster/python_modules/libraries/dagster-duckdb-pandas/dagster_duckdb_pandas_tests/data/{file}")
    data['region'] = context.asset_partition_key_for_output()

    return data

def test_dynamic_partition(tmp_path):
    with instance_for_test() as instance:
        duckdb_io_manager = duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        )
        resource_defs = {"io_manager": duckdb_io_manager}

        dynamic_regions.add_partitions(["northeast"], instance)

        materialize(
            [plant_data],
            partition_key="northeast",
            resources=resource_defs,
            instance=instance
        )

# # --- Sensors
# @sensor(job=asset_job)
# def watch_for_new_plant_data(context):
#     """Sensor watches for new data files to be processed"""

#     ls = DirectoryLister(directory="data")
#     cursor = context.cursor or None
#     already_seen = set()
#     if cursor is not None:
#         already_seen = set(ast.literal_eval(cursor))

#     files = set(ls.list())
#     new_files = files - already_seen

#     if len(new_files) == 0:
#         return SkipReason("No new files to process")


#     run_requests = []

#     for f in new_files:
#         partition_key=f.replace(".csv", "")
#         dynamic_regions.add_partitions([partition_key], context.instance)
#         run_requests.append(
#             asset_job.run_request_for_partition(
#                 partition_key=partition_key, instance=context.instance
#             )
#         )

#     context.update_cursor(str(files))
#     return run_requests
