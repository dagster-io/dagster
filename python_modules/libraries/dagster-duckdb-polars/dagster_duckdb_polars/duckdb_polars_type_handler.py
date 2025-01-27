from collections.abc import Sequence
from typing import Optional

import polars as pl
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_duckdb.io_manager import DuckDbClient, DuckDBIOManager, build_duckdb_io_manager


class DuckDBPolarsTypeHandler(DbTypeHandler[pl.DataFrame]):
    """Stores and loads Polars DataFrames in DuckDB.

    To use this type handler, return it from the ``type_handlers` method of an I/O manager that inherits from ``DuckDBIOManager``.

    Example:
        .. code-block:: python

            from dagster_duckdb import DuckDBIOManager
            from dagster_duckdb_polars import DuckDBPolarsTypeHandler

            class MyDuckDBIOManager(DuckDBIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [DuckDBPolarsTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb")}
            )

    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pl.DataFrame, connection
    ):
        """Stores the polars DataFrame in duckdb."""
        obj_arrow = obj.to_arrow()  # noqa: F841  # need obj_arrow symbol to exist for duckdb query
        connection.execute(f"create schema if not exists {table_slice.schema};")
        connection.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from"
            " obj_arrow;"
        )
        if not connection.fetchall():
            # table was not created, therefore already exists. Insert the data
            connection.execute(
                f"insert into {table_slice.schema}.{table_slice.table} select * from obj_arrow"
            )

        context.add_output_metadata(
            {
                "row_count": obj.shape[0],
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))
                            for name, dtype in zip(obj.columns, obj.dtypes)
                        ]
                    )
                ),
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pl.DataFrame:
        """Loads the input as a Polars DataFrame."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pl.DataFrame()
        select_statement = connection.execute(
            DuckDbClient.get_select_statement(table_slice=table_slice)
        )
        duckdb_to_arrow = select_statement.arrow()
        return pl.DataFrame(duckdb_to_arrow)

    @property
    def supported_types(self):
        return [pl.DataFrame]


duckdb_polars_io_manager = build_duckdb_io_manager(
    [DuckDBPolarsTypeHandler()], default_load_type=pl.DataFrame
)
duckdb_polars_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes polars dataframes to DuckDB. When
using the duckdb_polars_io_manager, any inputs and outputs without type annotations will be loaded
as Polars DataFrames.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_duckdb_polars import duckdb_polars_io_manager

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in DuckDB
        )
        def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_polars_io_manager.configured({"database": "my_db.duckdb"})}
        )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_polars_io_manager.configured({"database": "my_db.duckdb", "schema": "my_schema"})}
        )

    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pl.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
            )
            def my_other_table() -> pl.DataFrame:
                ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pl.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".


    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pl.DataFrame) -> pl.DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""


class DuckDBPolarsIOManager(DuckDBIOManager):
    """An I/O manager definition that reads inputs from and writes Polars DataFrames to DuckDB. When
    using the DuckDBPolarsIOManager, any inputs and outputs without type annotations will be loaded
    as Polars DataFrames.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_duckdb_polars import DuckDBPolarsIOManager

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in DuckDB
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBPolarsIOManager(database="my_db.duckdb")}
            )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": DuckDBPolarsIOManager(database="my_db.duckdb", schema="my_schema")}
        )

    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pl.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
            )
            def my_other_table() -> pl.DataFrame:
                ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pl.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pl.DataFrame) -> pl.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DuckDBPolarsTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pl.DataFrame
