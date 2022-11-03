import pandas as pd
from dagster_duckdb.io_manager import DuckDbClient, _connect_duckdb

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice


class DuckDBPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Stores and loads Pandas DataFrames in DuckDB.

    To use this type handler, pass it to ``build_duckdb_io_manager``

    Example:
        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            @asset
            def my_table():
                ...

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": duckdb_io_manager.configured({"database": "my_db.duckdb"})}
                )

    """

    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame):
        """Stores the pandas DataFrame in duckdb."""

        conn = _connect_duckdb(context).cursor()

        conn.execute(f"create schema if not exists {table_slice.schema};")
        conn.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from obj;"
        )
        if not conn.fetchall():
            # table was not created, therefore already exists. Insert the data
            conn.execute(f"insert into {table_slice.schema}.{table_slice.table} select * from obj")

        context.add_output_metadata(
            {
                "row_count": obj.shape[0],
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in obj.dtypes.iteritems()
                        ]
                    )
                ),
            }
        )

    def load_input(self, context: InputContext, table_slice: TableSlice) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        conn = _connect_duckdb(context).cursor()
        return conn.execute(DuckDbClient.get_select_statement(table_slice)).fetchdf()

    @property
    def supported_types(self):
        return [pd.DataFrame]
