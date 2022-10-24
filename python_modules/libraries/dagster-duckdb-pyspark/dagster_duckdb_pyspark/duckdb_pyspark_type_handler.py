import pyspark
from dagster_duckdb.io_manager import DuckDbClient, _connect_duckdb
from pyspark.sql import SparkSession

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice


class DuckDBPySparkTypeHandler(DbTypeHandler[pyspark.sql.DataFrame]):
    """Stores PySpark DataFrames in DuckDB.

    **Note:** This type handler can only store outputs. It cannot currently load inputs.

    To use this type handler, pass it to ``build_duckdb_io_manager``

    Example:
        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler

            @asset
            def my_table():
                ...

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])

            @repository
            def my_repo():
                return with_resources(
                    [my_table],
                    {"io_manager": duckdb_io_manager.configured({"database": "my_db.duckdb"})}
                )
    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pyspark.sql.DataFrame
    ):
        """Stores the given object at the provided filepath."""
        conn = _connect_duckdb(context).cursor()

        pd_df = obj.toPandas()  # pylint: disable=unused-variable; pd_df is used in duckdb queries

        conn.execute(f"create schema if not exists {table_slice.schema};")
        conn.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from pd_df;"
        )
        if not conn.fetchall():
            # table was not created, therefore already exists. Insert the data
            conn.execute(
                f"insert into {table_slice.schema}.{table_slice.table} select * from pd_df"
            )

        context.add_output_metadata(
            {
                "row_count": obj.count(),
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype)) for name, dtype in obj.dtypes
                        ]
                    )
                ),
            }
        )

    def load_input(self, context: InputContext, table_slice: TableSlice) -> pyspark.sql.DataFrame:
        """Loads the return of the query as the correct type."""
        conn = _connect_duckdb(context).cursor()
        pd_df = conn.execute(DuckDbClient.get_select_statement(table_slice)).fetchdf()
        spark = SparkSession.builder.getOrCreate()
        return spark.createDataFrame(pd_df)

    @property
    def supported_types(self):
        return [pyspark.sql.DataFrame]
