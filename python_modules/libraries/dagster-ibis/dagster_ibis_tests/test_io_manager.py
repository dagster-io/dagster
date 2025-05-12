from datetime import datetime

import ibis
import ibis.expr.types as ir
import pandas as pd
import pytest
from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    In,
    Out,
    StaticPartitionsDefinition,
    asset,
    job,
    materialize,
    op,
)
from dagster_ibis import IbisIOManager


# Fixture for a temporary DuckDB database
@pytest.fixture
def duckdb_path(tmp_path):
    return (tmp_path / "my_db.duckdb").as_posix()


def test_ibis_io_manager_with_assets(duckdb_path):
    """Test the IbisIOManager with assets."""

    # Define assets
    @asset
    def source_table() -> ir.Table:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        return ibis.memtable(df)

    @asset
    def downstream_table(source_table: ir.Table) -> ir.Table:
        # Transform the source table
        return source_table.mutate(c=source_table.a + source_table.b)

    # Create definitions with IbisIOManager
    defs = Definitions(
        assets=[source_table, downstream_table],
        resources={
            "io_manager": IbisIOManager(backend="duckdb", database=duckdb_path, schema="my_schema")
        },
    )

    # Materialize assets directly
    result = materialize(
        [source_table, downstream_table],
        resources={
            "io_manager": IbisIOManager(backend="duckdb", database=duckdb_path, schema="my_schema")
        },
    )
    assert result.success

    # Verify the tables were created
    conn = ibis.duckdb.connect(duckdb_path)
    assert "my_schema" in conn.list_databases()
    assert "source_table" in conn.list_tables(database="my_schema")
    assert "downstream_table" in conn.list_tables(database="my_schema")

    # Verify the data
    source = conn.table("source_table", database="my_schema")
    downstream = conn.table("downstream_table", database="my_schema")

    # Execute and convert to pandas to verify data
    source_df = source.execute()
    downstream_df = downstream.execute()

    assert len(source_df) == 3
    assert len(downstream_df) == 3
    assert "c" in downstream_df.columns
    assert (downstream_df["c"] == downstream_df["a"] + downstream_df["b"]).all()


def test_ibis_io_manager_with_ops(duckdb_path):
    """Test the IbisIOManager with ops."""

    # Define ops
    @op(out={"source_table": Out(dagster_type=ir.Table)})
    def make_table():
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        return ibis.memtable(df)

    @op(
        ins={"source_table": In(dagster_type=ir.Table)},
        out={"downstream_table": Out(dagster_type=ir.Table)},
    )
    def transform_table(source_table):
        # Transform the source table
        return source_table.mutate(c=source_table.a + source_table.b)

    # Define job
    @job(
        resource_defs={
            "io_manager": IbisIOManager(
                backend="duckdb", database=duckdb_path, schema="test_schema"
            )
        }
    )
    def ibis_job():
        transform_table(make_table())

    # Execute job
    result = ibis_job.execute_in_process()
    assert result.success

    # Verify the tables were created
    conn = ibis.duckdb.connect(duckdb_path)
    assert "test_schema" in conn.list_databases()
    assert "source_table" in conn.list_tables(database="test_schema")
    assert "downstream_table" in conn.list_tables(database="test_schema")

    # Verify the data
    output_table = conn.table("downstream_table", database="test_schema")
    output_df = output_table.execute()

    assert len(output_df) == 3
    assert "c" in output_df.columns
    assert (output_df["c"] == output_df["a"] + output_df["b"]).all()


def test_ibis_io_manager_with_static_partitions(duckdb_path):
    """Test the IbisIOManager with static partitions."""
    # Define partitions
    color_partitions_def = StaticPartitionsDefinition(["red", "green", "blue"])

    # Define partitioned assets
    @asset(partitions_def=color_partitions_def, metadata={"partition_expr": "color"})
    def partitioned_data(context) -> ir.Table:
        color = context.partition_key
        if color == "red":
            values = [1, 2, 3]
        elif color == "green":
            values = [4, 5, 6]
        else:  # blue
            values = [7, 8, 9]

        df = pd.DataFrame({"value": values, "color": [color] * len(values)})
        return ibis.memtable(df)

    @asset(partitions_def=color_partitions_def, metadata={"partition_expr": "color"})
    def doubled_data(context, partitioned_data: ir.Table) -> ir.Table:
        # Double the values
        return partitioned_data.mutate(doubled=partitioned_data.value * 2)

    # Create definitions
    defs = Definitions(
        assets=[partitioned_data, doubled_data],
        resources={
            "io_manager": IbisIOManager(
                backend="duckdb", database=duckdb_path, schema="partitioned"
            )
        },
    )

    # Materialize one partition at a time
    for color in ["red", "green", "blue"]:
        result = materialize(
            [partitioned_data, doubled_data],
            partition_key=color,
            resources={
                "io_manager": IbisIOManager(
                    backend="duckdb", database=duckdb_path, schema="partitioned"
                )
            },
        )
        assert result.success

    # Verify all partitions
    conn = ibis.duckdb.connect(duckdb_path)
    assert "partitioned" in conn.list_databases()

    # Check partitioned_data table
    assert "partitioned_data" in conn.list_tables(database="partitioned")
    data_table = conn.table("partitioned_data", database="partitioned")
    data_df = data_table.execute()

    # Check doubled_data table
    assert "doubled_data" in conn.list_tables(database="partitioned")
    doubled_table = conn.table("doubled_data", database="partitioned")
    doubled_df = doubled_table.execute()

    # Verify data
    assert len(data_df) == 9  # 3 values for each of the 3 partitions
    assert set(data_df["color"]) == {"red", "green", "blue"}
    assert len(doubled_df) == 9
    assert (doubled_df["doubled"] == doubled_df["value"] * 2).all()

    # Verify each partition contains the correct data
    for color in ["red", "green", "blue"]:
        filtered_data = data_df[data_df["color"] == color]
        if color == "red":
            assert set(filtered_data["value"]) == {1, 2, 3}
        elif color == "green":
            assert set(filtered_data["value"]) == {4, 5, 6}
        else:  # blue
            assert set(filtered_data["value"]) == {7, 8, 9}


def test_ibis_io_manager_with_time_partitions(duckdb_path):
    """Test the IbisIOManager with time-based partitions."""
    # Define time-based partitions
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 4)  # Exclusive
    daily_partitions_def = DailyPartitionsDefinition(start_date=start_date, end_date=end_date)

    # Define partitioned assets
    @asset(partitions_def=daily_partitions_def, metadata={"partition_expr": "date"})
    def daily_data(context) -> ir.Table:
        # Parse the partition key to get the date
        partition_date = datetime.strptime(context.partition_key, "%Y-%m-%d")

        # Generate some data for this date
        df = pd.DataFrame(
            {
                "value": [1, 2, 3],
                "date": [partition_date.date()] * 3,
                "day_of_week": [partition_date.strftime("%A")] * 3,
            }
        )
        return ibis.memtable(df)

    @asset(partitions_def=daily_partitions_def, metadata={"partition_expr": "date"})
    def aggregated_daily_data(context, daily_data: ir.Table) -> ir.Table:
        # Aggregate the data
        return daily_data.group_by("date").aggregate(
            total_value=daily_data.value.sum(),
            avg_value=daily_data.value.mean(),
            count=daily_data.count(),
        )

    # Create definitions
    defs = Definitions(
        assets=[daily_data, aggregated_daily_data],
        resources={
            "io_manager": IbisIOManager(
                backend="duckdb", database=duckdb_path, schema="time_partitioned"
            )
        },
    )

    # Materialize each daily partition
    partition_keys = ["2023-01-01", "2023-01-02", "2023-01-03"]
    for key in partition_keys:
        result = materialize(
            [daily_data, aggregated_daily_data],
            partition_key=key,
            resources={
                "io_manager": IbisIOManager(
                    backend="duckdb", database=duckdb_path, schema="time_partitioned"
                )
            },
        )
        assert result.success

    # Verify the tables were created
    conn = ibis.duckdb.connect(duckdb_path)
    assert "time_partitioned" in conn.list_databases()
    assert "daily_data" in conn.list_tables(database="time_partitioned")
    assert "aggregated_daily_data" in conn.list_tables(database="time_partitioned")

    # Verify the data
    daily_table = conn.table("daily_data", database="time_partitioned")
    daily_df = daily_table.execute()

    agg_table = conn.table("aggregated_daily_data", database="time_partitioned")
    agg_df = agg_table.execute()

    # Verify the daily data
    assert len(daily_df) == 9  # 3 values per day for 3 days

    # Verify the aggregated data
    assert len(agg_df) == 3  # One aggregated record per day
    for date_str in partition_keys:
        date_val = datetime.strptime(date_str, "%Y-%m-%d")
        date_agg = agg_df[agg_df["date"] == date_val]
        assert len(date_agg) == 1
        assert date_agg.iloc[0]["total_value"] == 6  # 1+2+3
        assert date_agg.iloc[0]["avg_value"] == 2  # (1+2+3)/3
        assert date_agg.iloc[0]["count"] == 3
