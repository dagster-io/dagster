import os
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import ibis
import pandas as pd
import pytest
from dagster import AssetIn, asset, materialize
from dagster_ibis import IbisIOManager
from dagster_snowflake.resources import SnowflakeResource

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_SNOWFLAKE_CONF: Mapping[str, Any] = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": "BUILDKITE",
    "password": os.getenv("SNOWFLAKE_BUILDKITE_PASSWORD", ""),
}

DATABASE = "TEST_SNOWFLAKE_IO_MANAGER"
SCHEMA = "SNOWFLAKE_IO_MANAGER_SCHEMA"


@contextmanager
def temporary_snowflake_table(schema_name: str, db_name: str) -> Iterator[str]:
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    with SnowflakeResource(
        database=db_name, **SHARED_BUILDKITE_SNOWFLAKE_CONF
    ).get_connection() as conn:
        try:
            yield table_name
        finally:
            conn.cursor().execute(f"drop table {schema_name}.{table_name}")


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
@pytest.mark.integration
def test_ibis_io_manager_with_assets():
    """Test the IbisIOManager with assets."""
    with (
        temporary_snowflake_table(
            schema_name=SCHEMA,
            db_name=DATABASE,
        ) as source_table,
        temporary_snowflake_table(
            schema_name=SCHEMA,
            db_name=DATABASE,
        ) as downstream_table,
    ):
        # Define assets
        @asset(key_prefix=SCHEMA, name=source_table)
        def source_table() -> pd.DataFrame:
            df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            return df

        @asset(
            key_prefix=SCHEMA,
            name=downstream_table,
            ins={"source_table": AssetIn([SCHEMA, source_table])},
        )
        def downstream_table(source_table: pd.DataFrame) -> pd.DataFrame:
            # Transform the source table
            source_table["c"] = source_table["a"] + source_table["b"]
            return source_table

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            # Materialize assets directly
            result = materialize(
                [source_table, downstream_table],
                resources={
                    "io_manager": IbisIOManager(
                        backend="snowflake",
                        database=DATABASE,
                        schema=SCHEMA,
                        **SHARED_BUILDKITE_SNOWFLAKE_CONF,
                    )
                },
            )
            assert result.success

            # Verify the tables were created
            conn = ibis.snowflake.connect(
                database=DATABASE,
                schema=SCHEMA,
                **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            )
            assert SCHEMA in conn.list_databases()
            assert source_table in conn.list_tables(database=SCHEMA)
            assert downstream_table in conn.list_tables(database=SCHEMA)

            # Verify the data
            source = conn.table(source_table, database=SCHEMA)
            downstream = conn.table(downstream_table, database=SCHEMA)

            # Execute and convert to pandas to verify data
            source_df = source.execute()
            downstream_df = downstream.execute()

            assert len(source_df) == 3
            assert len(downstream_df) == 3
            assert "c" in downstream_df.columns
            assert (downstream_df["c"] == downstream_df["a"] + downstream_df["b"]).all()

            conn.disconnect()


# def test_ibis_io_manager_with_ops(duckdb_path):
#     """Test the IbisIOManager with ops."""
#
#     # Define ops
#     @op(out={"source_table": Out(dagster_type=pd.DataFrame)})
#     def make_table():
#         df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
#         return df
#
#     @op(
#         ins={"source_table": In(dagster_type=pd.DataFrame)},
#         out={"downstream_table": Out(dagster_type=pd.DataFrame)},
#     )
#     def transform_table(source_table):
#         # Transform the source table
#         source_table["c"] = source_table["a"] + source_table["b"]
#         return source_table
#
#     # Define job
#     @job(
#         resource_defs={
#             "io_manager": IbisIOManager(
#                 backend="duckdb", database=duckdb_path, schema="test_schema"
#             )
#         }
#     )
#     def ibis_job():
#         transform_table(make_table())
#
#     # run the job twice to ensure that tables get properly deleted
#     for _ in range(2):
#         # Execute job
#         result = ibis_job.execute_in_process()
#         assert result.success
#
#         # Verify the tables were created
#         conn = ibis.duckdb.connect(duckdb_path)
#         assert "test_schema" in conn.list_databases()
#         assert "source_table" in conn.list_tables(database="test_schema")
#         assert "downstream_table" in conn.list_tables(database="test_schema")
#
#         # Verify the data
#         output_table = conn.table("downstream_table", database="test_schema")
#         output_df = output_table.execute()
#
#         assert len(output_df) == 3
#         assert "c" in output_df.columns
#         assert (output_df["c"] == output_df["a"] + output_df["b"]).all()
#
#         conn.disconnect()


# def test_ibis_io_manager_with_static_partitions(duckdb_path):
#     """Test the IbisIOManager with static partitions."""
#     # Define partitions
#     color_partitions_def = StaticPartitionsDefinition(["red", "green", "blue"])
#
#     # Define partitioned assets
#     @asset(partitions_def=color_partitions_def, metadata={"partition_expr": "color"})
#     def partitioned_data(context) -> pd.DataFrame:
#         color = context.partition_key
#         if color == "red":
#             values = [1, 2, 3]
#         elif color == "green":
#             values = [4, 5, 6]
#         else:  # blue
#             values = [7, 8, 9]
#
#         df = pd.DataFrame({"value": values, "color": [color] * len(values)})
#         return df
#
#     @asset(partitions_def=color_partitions_def, metadata={"partition_expr": "color"})
#     def doubled_data(context, partitioned_data: pd.DataFrame) -> pd.DataFrame:
#         # Double the values
#         partitioned_data["doubled"] = partitioned_data["value"] * 2
#         return partitioned_data
#
#     # materialize asset twice to ensure that partitions get properly deleted
#     for _ in range(2):
#         # Materialize one partition at a time
#         for color in ["red", "green", "blue"]:
#             result = materialize(
#                 [partitioned_data, doubled_data],
#                 partition_key=color,
#                 resources={
#                     "io_manager": IbisIOManager(
#                         backend="duckdb", database=duckdb_path, schema="partitioned"
#                     )
#                 },
#             )
#             assert result.success
#
#         # Verify all partitions
#         conn = ibis.duckdb.connect(duckdb_path)
#         assert "partitioned" in conn.list_databases()
#
#         # Check partitioned_data table
#         assert "partitioned_data" in conn.list_tables(database="partitioned")
#         data_table = conn.table("partitioned_data", database="partitioned")
#         data_df = data_table.execute()
#
#         # Check doubled_data table
#         assert "doubled_data" in conn.list_tables(database="partitioned")
#         doubled_table = conn.table("doubled_data", database="partitioned")
#         doubled_df = doubled_table.execute()
#
#         # Verify data
#         assert len(data_df) == 9  # 3 values for each of the 3 partitions
#         assert set(data_df["color"]) == {"red", "green", "blue"}
#         assert len(doubled_df) == 9
#         assert (doubled_df["doubled"] == doubled_df["value"] * 2).all()
#
#         # Verify each partition contains the correct data
#         for color in ["red", "green", "blue"]:
#             filtered_data = data_df[data_df["color"] == color]
#             if color == "red":
#                 assert set(filtered_data["value"]) == {1, 2, 3}
#             elif color == "green":
#                 assert set(filtered_data["value"]) == {4, 5, 6}
#             else:  # blue
#                 assert set(filtered_data["value"]) == {7, 8, 9}
#
#         conn.disconnect()
#
#
# def test_ibis_io_manager_with_time_partitions(duckdb_path):
#     """Test the IbisIOManager with time-based partitions."""
#     # Define time-based partitions
#     start_date = datetime(2023, 1, 1)
#     end_date = datetime(2023, 1, 4)  # Exclusive
#     daily_partitions_def = DailyPartitionsDefinition(start_date=start_date, end_date=end_date)
#
#     # Define partitioned assets
#     @asset(partitions_def=daily_partitions_def, metadata={"partition_expr": "date"})
#     def daily_data(context) -> pd.DataFrame:
#         # Parse the partition key to get the date
#         partition_date = datetime.strptime(context.partition_key, "%Y-%m-%d")
#
#         # Generate some data for this date
#         df = pd.DataFrame(
#             {
#                 "value": [1, 2, 3],
#                 "date": [partition_date.date()] * 3,
#                 "day_of_week": [partition_date.strftime("%A")] * 3,
#             }
#         )
#         return df
#
#     @asset(partitions_def=daily_partitions_def, metadata={"partition_expr": "date"})
#     def aggregated_daily_data(context, daily_data: pd.DataFrame) -> pd.DataFrame:
#         # Aggregate the data
#         return daily_data.groupby("date", as_index=False).agg(
#             total_value=pd.NamedAgg(column="value", aggfunc="sum"),
#             avg_value=pd.NamedAgg(column="value", aggfunc="mean"),
#             count=pd.NamedAgg(column="value", aggfunc="count"),
#         )
#
#     # materialize asset twice to ensure that partitions get properly deleted
#     for _ in range(2):
#         # Materialize each daily partition
#         partition_keys = ["2023-01-01", "2023-01-02", "2023-01-03"]
#         for key in partition_keys:
#             result = materialize(
#                 [daily_data, aggregated_daily_data],
#                 partition_key=key,
#                 resources={
#                     "io_manager": IbisIOManager(
#                         backend="duckdb", database=duckdb_path, schema="time_partitioned"
#                     )
#                 },
#             )
#             assert result.success
#
#         # Verify the tables were created
#         conn = ibis.duckdb.connect(duckdb_path)
#         assert "time_partitioned" in conn.list_databases()
#         assert "daily_data" in conn.list_tables(database="time_partitioned")
#         assert "aggregated_daily_data" in conn.list_tables(database="time_partitioned")
#
#         # Verify the data
#         daily_table = conn.table("daily_data", database="time_partitioned")
#         daily_df = daily_table.execute()
#
#         agg_table = conn.table("aggregated_daily_data", database="time_partitioned")
#         agg_df = agg_table.execute()
#
#         # Verify the daily data
#         assert len(daily_df) == 9  # 3 values per day for 3 days
#
#         # Verify the aggregated data
#         assert len(agg_df) == 3  # One aggregated record per day
#         for date_str in partition_keys:
#             date_val = datetime.strptime(date_str, "%Y-%m-%d")
#             date_agg = agg_df[agg_df["date"] == date_val]
#             assert len(date_agg) == 1
#             assert date_agg.iloc[0]["total_value"] == 6  # 1+2+3
#             assert date_agg.iloc[0]["avg_value"] == 2  # (1+2+3)/3
#             assert date_agg.iloc[0]["count"] == 3
#
#         conn.disconnect()
