from typing import Mapping, Optional

import pandas as pd
from dagster_duckdb.io_manager import (
    DuckDbClient,
    _connect_duckdb,
    build_duckdb_io_manager,
    get_duckdb_io_manager_config_schema,
)

from dagster import Field, InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._config.field_utils import convert_potential_field
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster._core.storage.io_manager import IOManagerDefinition


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


duckdb_pandas_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])
duckdb_pandas_io_manager.__doc__ = """
An IO manager definition that reads inputs from and writes pandas dataframes to DuckDB.

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

        @repository
        def my_repo():
            return with_resources(
                [my_table],
                {"io_manager": duckdb_pandas_io_manager.configured({"database": "my_db.duckdb"})}
            )

    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the IO Manager. For assets, the schema will be determined from the asset key.
    For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
    via config or on the asset/op, "public" will be used for the schema.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> pd.DataFrame:
            # the returned value will be stored at my_schema.my_table
            ...

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


def apply_defaults(defaults: dict, config_schema: Mapping[str, Field]):
    new_config_schema = {}
    for key, value in config_schema.items():
        old_field = convert_potential_field(value)
        default_value = defaults[key]
        new_config_schema[key] = (
            Field(
                config=old_field.config_type,
                description=old_field.description,
                is_required=False,
                default_value=default_value,
            )
            if default_value
            else Field(
                config=old_field.config_type,
                description=old_field.description,
                is_required=False,
            )
        )
    return new_config_schema


class DuckDbPandasIOManager(IOManagerDefinition):
    def __init__(self, database: str, schema: Optional[str] = None):
        super().__init__(
            resource_fn=duckdb_pandas_io_manager.resource_fn,
            config_schema=apply_defaults(
                dict(database=database, schema=schema), get_duckdb_io_manager_config_schema()
            ),
        )


# class DuckDbPandasIOManager(IOManagerDefinition):
#     def __init__(self, database: str, schema: Optional[str] = None):
#         super().__init__(
#             resource_fn=lambda _: DbIOManager(
#                 type_handlers=[DuckDBPandasTypeHandler()],
#                 db_client=DuckDbClient(),
#                 io_manager_name="DuckDBIOManager",
#             ),
#             config_schema={

#                 "database": Field(
#                     StringSource,
#                     description="Path to the DuckDB database.",
#                     default_value=database,
#                     is_required=False,
#                 ),
#                 "schema": Field(
#                     StringSource,
#                     description="Name of the schema to use.",
#                     is_required=False,
#                     default_value=schema,
#                 )
#                 if schema
#                 else Field(
#                     StringSource,
#                     description="Name of the schema to use.",
#                     is_required=False,
#                 ),
#             },
#         )
