import pandas as pd
from dagster_duckdb.io_manager import (
    DuckDbClient,
    DuckDbIOManagerConfigSchema,
    _connect_duckdb,
    build_duckdb_io_manager,
)

from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._config.field_utils import config_dictionary_from_values
from dagster._config.structured_config import StructuredIOManagerAdapter
from dagster._core.definitions.definition_config_schema import (
    ConfiguredDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
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


class ConfiguredIOManagerAdapter(IOManagerDefinition):
    def __init__(self, parent_io_manager, args):
        ## TODO: coerce all strings to string source
        super().__init__(
            resource_fn=parent_io_manager.resource_fn,
            config_schema=ConfiguredDefinitionConfigSchema(
                parent_io_manager,
                convert_user_facing_definition_config_schema(
                    None
                ),  # this is actually just replicating a bug that allows for too permissive of config
                config_dictionary_from_values(
                    args,
                    parent_io_manager.config_schema.as_field(),
                ),
            ),
        )


class DuckDbPandasIOManager(DuckDbIOManagerConfigSchema, StructuredIOManagerAdapter):
    @property
    def wrapped_io_manager(self) -> IOManagerDefinition:
        return duckdb_pandas_io_manager
