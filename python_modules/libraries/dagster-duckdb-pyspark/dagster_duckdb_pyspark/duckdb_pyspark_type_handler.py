from collections.abc import Sequence
from typing import Optional

import pyarrow as pa
import pyspark
import pyspark.sql
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_duckdb.io_manager import DuckDbClient, DuckDBIOManager, build_duckdb_io_manager
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType


def pyspark_df_to_arrow_table(df: pyspark.sql.DataFrame) -> pa.Table:
    """Converts a PySpark DataFrame to a PyArrow Table."""
    # `_collect_as_arrow` API call sourced from:
    #   https://stackoverflow.com/questions/73203318/how-to-transform-spark-dataframe-to-polars-dataframe
    return pa.Table.from_batches(df._collect_as_arrow())  # noqa: SLF001


class DuckDBPySparkTypeHandler(DbTypeHandler[pyspark.sql.DataFrame]):
    """Stores PySpark DataFrames in DuckDB.

    To use this type handler, return it from the ``type_handlers` method of an I/O manager that inherits from ``DuckDBIOManager``.

    Example:
        .. code-block:: python

            from dagster_duckdb import DuckDBIOManager
            from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler

            class MyDuckDBIOManager(DuckDBIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [DuckDBPySparkTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pyspark.sql.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb")}
            )
    """

    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: pyspark.sql.DataFrame,
        connection,
    ):
        """Stores the given object at the provided filepath."""
        pa_df = pyspark_df_to_arrow_table(obj)  # noqa: F841
        connection.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from"
            " pa_df;"
        )
        if not connection.fetchall():
            # table was not created, therefore already exists. Insert the data
            connection.execute(
                f"insert into {table_slice.schema}.{table_slice.table} select * from pa_df;"
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

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pyspark.sql.DataFrame:
        """Loads the return of the query as the correct type."""
        spark = SparkSession.builder.getOrCreate()  # type: ignore
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return spark.createDataFrame([], StructType([]))

        pd_df = connection.execute(DuckDbClient.get_select_statement(table_slice)).fetchdf()
        return spark.createDataFrame(pd_df)

    @property
    def supported_types(self):
        return [pyspark.sql.DataFrame]


duckdb_pyspark_io_manager = build_duckdb_io_manager(
    [DuckDBPySparkTypeHandler()], default_load_type=pyspark.sql.DataFrame
)
duckdb_pyspark_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes PySpark DataFrames to DuckDB. When
using the duckdb_pyspark_io_manager, any inputs and outputs without type annotations will be loaded
as PySpark DataFrames.

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

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_pyspark_io_manager.configured({"database": "my_db.duckdb"})}
        )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_pyspark_io_manager.configured({"database": "my_db.duckdb", "schema": "my_schema"})}
        )

    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pyspark.sql.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
            )
            def my_other_table() -> pyspark.sql.DataFrame:
                ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pyspark.sql.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

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


class DuckDBPySparkIOManager(DuckDBIOManager):
    """An I/O manager definition that reads inputs from and writes PySpark DataFrames to DuckDB. When
    using the DuckDBPySparkIOManager, any inputs and outputs without type annotations will be loaded
    as PySpark DataFrames.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_duckdb_pyspark import DuckDBPySparkIOManager

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in DuckDB
            )
            def my_table() -> pyspark.sql.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBPySparkIOManager(database="my_db.duckdb")}
            )

        You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBPySparkIOManager(database="my_db.duckdb", schema="my_schema")}
            )

        On individual assets, you an also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

                @asset(
                    key_prefix=["my_schema"]  # will be used as the schema in duckdb
                )
                def my_table() -> pyspark.sql.DataFrame:
                    ...

                @asset(
                    metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
                )
                def my_other_table() -> pyspark.sql.DataFrame:
                    ...

        For ops, the schema can be specified by including a "schema" entry in output metadata.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pyspark.sql.DataFrame:
                ...

        If none of these is provided, the schema will default to "public".

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

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DuckDBPySparkTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pyspark.sql.DataFrame
