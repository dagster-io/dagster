from collections.abc import Sequence
from typing import Optional

import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_duckdb.io_manager import DuckDbClient, DuckDBIOManager, build_duckdb_io_manager


class DuckDBPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Stores and loads Pandas DataFrames in DuckDB.

    To use this type handler, return it from the ``type_handlers` method of an I/O manager that inherits from ``DuckDBIOManager``.

    Example:
        .. code-block:: python

            from dagster_duckdb import DuckDBIOManager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            class MyDuckDBIOManager(DuckDBIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [DuckDBPandasTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb")}
            )

    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection
    ):
        """Stores the pandas DataFrame in duckdb."""
        connection.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as select * from"
            " obj;"
        )
        if not connection.fetchall():
            # table was not created, therefore already exists. Insert the data
            connection.execute(
                f"insert into {table_slice.schema}.{table_slice.table} select * from obj"
            )

        context.add_output_metadata(
            {
                # output object may be a slice/partition, so we output different metadata keys based on
                # whether this output represents an entire table or just a slice/partition
                **(
                    TableMetadataSet(partition_row_count=obj.shape[0])
                    if context.has_partition_key
                    else TableMetadataSet(row_count=obj.shape[0])
                ),
                "dataframe_columns": MetadataValue.table_schema(
                    TableSchema(
                        columns=[
                            TableColumn(name=name, type=str(dtype))  # type: ignore  # (bad stubs)
                            for name, dtype in obj.dtypes.items()
                        ]
                    )
                ),
            }
        )

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pd.DataFrame()
        return connection.execute(DuckDbClient.get_select_statement(table_slice)).fetchdf()

    @property
    def supported_types(self):
        return [pd.DataFrame]


duckdb_pandas_io_manager = build_duckdb_io_manager(
    [DuckDBPandasTypeHandler()], default_load_type=pd.DataFrame
)
duckdb_pandas_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes Pandas DataFrames to DuckDB. When
using the duckdb_pandas_io_manager, any inputs and outputs without type annotations will be loaded
as Pandas DataFrames.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_duckdb_pandas import duckdb_pandas_io_manager

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in DuckDB
        )
        def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
            ...

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_pandas_io_manager.configured({"database": "my_db.duckdb"})}
        )

    You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
    Manager. This schema will be used if no other schema is specified directly on an asset or op.

    .. code-block:: python

        defs = Definitions(
            assets=[my_table],
            resources={"io_manager": duckdb_pandas_io_manager.configured({"database": "my_db.duckdb", "schema": "my_schema"})}
        )

    On individual assets, you an also specify the schema where they should be stored using metadata or
    by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
    take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in duckdb
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
        )
        def my_other_table() -> pd.DataFrame:
            ...

    For ops, the schema can be specified by including a "schema" entry in output metadata.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            ...

    If none of these is provided, the schema will default to "public".

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""


class DuckDBPandasIOManager(DuckDBIOManager):
    """An I/O manager definition that reads inputs from and writes Pandas DataFrames to DuckDB. When
    using the DuckDBPandasIOManager, any inputs and outputs without type annotations will be loaded
    as Pandas DataFrames.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_duckdb_pandas import DuckDBPandasIOManager

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in DuckDB
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBPandasIOManager(database="my_db.duckdb")}
            )

        You can set a default schema to store the assets using the ``schema`` configuration value of the DuckDB I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBPandasIOManager(database="my_db.duckdb", schema="my_schema")}
            )

        On individual assets, you an also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> pd.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in duckdb
            )
            def my_other_table() -> pd.DataFrame:
                ...

        For ops, the schema can be specified by including a "schema" entry in output metadata.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> pd.DataFrame:
                ...

        If none of these is provided, the schema will default to "public".

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
                # my_table will just contain the data from column "a"
                ...

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DuckDBPandasTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pd.DataFrame
