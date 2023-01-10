import pyspark
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_duckdb.io_manager import DuckDbClient, _connect_duckdb, build_duckdb_io_manager
from pyspark.sql import SparkSession


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

        pd_df = obj.toPandas()  # noqa: F841

        conn.execute(f"create schema if not exists {table_slice.schema};")
        conn.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from"
            " pd_df;"
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


duckdb_pyspark_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])
duckdb_pyspark_io_manager.__doc__ = """
An IO manager definition that reads inputs from and writes PySpark DataFrames to DuckDB.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_duckdb_pyspark import duckdb_pyspark_io_manager

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in DuckDB
        )
        def my_table() -> pyspark.sql.DataFrame:  # the name of the asset will be the table name
            ...

        @repository
        def my_repo():
            return with_resources(
                [my_table],
                {"io_manager": duckdb_pyspark_io_manager.configured({"database": "my_db.duckdb"})}
            )

    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the IO Manager. For assets, the schema will be determined from the asset key.
    For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
    via config or on the asset/op, "public" will be used for the schema.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pyspark.sql.DataFrame:
            # the returned value will be stored at my_schema.my_table
            ...

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pyspark.sql.DataFrame) -> pyspark.sql.DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""
