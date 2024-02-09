from dagster import DataVersion, observable_source_asset

from .resource import DeltaTableResource

"""
Running the following code on an existing delta table gets you the last updated timestamp:
deltaTable.history(1).select("timestamp").collect()[0][0]
"""


@observable_source_asset
def observe_table_last_modified_time(context, delta_table: DeltaTableResource) -> DataVersion:
    table = delta_table.load()
    timestamp = table.history(1)[0]["timestamp"]
    # context.log.info the last modified time as a UTC timestamp.
    context.log.info(f"Last modified time for table {table}: {timestamp}")
    return DataVersion(str(timestamp))
