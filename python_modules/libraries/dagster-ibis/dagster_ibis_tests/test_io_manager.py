import ibis
import ibis.expr.types as ir
import pandas as pd
import pytest
from dagster import Definitions, In, Out, asset, job, materialize, op
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
    assert "my_schema" in conn.list_schemas()
    assert "source_table" in conn.list_tables(schema="my_schema")
    assert "downstream_table" in conn.list_tables(schema="my_schema")

    # Verify the data
    source = conn.table("source_table", schema="my_schema")
    downstream = conn.table("downstream_table", schema="my_schema")

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
    @op(out=Out(dagster_type=ir.Table))
    def make_table():
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        return ibis.memtable(df)

    @op(ins={"table": In(dagster_type=ir.Table)}, out=Out(dagster_type=ir.Table))
    def transform_table(table):
        return table.mutate(c=table.a * 2)

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
    assert "test_schema" in conn.list_schemas()
    assert "make_table" in conn.list_tables(schema="test_schema")
    assert "transform_table" in conn.list_tables(schema="test_schema")

    # Verify the data
    output_table = conn.table("transform_table", schema="test_schema")
    output_df = output_table.execute()

    assert len(output_df) == 3
    assert "c" in output_df.columns
    assert (output_df["c"] == output_df["a"] * 2).all()
