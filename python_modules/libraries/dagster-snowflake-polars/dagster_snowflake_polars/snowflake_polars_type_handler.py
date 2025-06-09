from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from typing import Optional

import polars as pl
from adbc_driver_manager import ProgrammingError
from adbc_driver_snowflake import dbapi
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema, io_manager
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.storage.db_io_manager import DbIOManager, DbTypeHandler, TableSlice
from dagster_snowflake import SnowflakeResource
from dagster_snowflake.snowflake_io_manager import (
    SnowflakeDbClient,
    SnowflakeIOManager,
    _get_cleanup_statement,
)


class SnowflakeAdbcClient(SnowflakeDbClient):
    @staticmethod
    @contextmanager
    def connect(context, table_slice):
        no_schema_config = (
            {k: v for k, v in context.resource_config.items() if k != "schema"}
            if context.resource_config
            else {}
        )
        with SnowflakeResource(
            schema=table_slice.schema, connector="adbc", **no_schema_config
        ).get_connection(raw_conn=False) as conn:
            yield conn

    @staticmethod
    def ensure_schema_exists(
        context: OutputContext, table_slice: TableSlice, connection: dbapi.Connection
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"show schemas like '{table_slice.schema}' in database {table_slice.database}"
            )
            schemas = cursor.fetchall()

        if len(schemas) == 0:
            with connection.cursor() as cursor:
                cursor.execute(f"create schema {table_slice.schema};")

    @staticmethod
    def delete_table_slice(context: OutputContext, table_slice: TableSlice, connection) -> None:
        try:
            connection.cursor().execute(_get_cleanup_statement(table_slice))
        except ProgrammingError as e:
            if any("does not exist" in arg for arg in e.args):
                # table doesn't exist yet, so ignore the error
                return
            else:
                raise


def _table_exists(table_slice: TableSlice, connection):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SHOW TABLES LIKE '{table_slice.table}' IN SCHEMA"
            f" {table_slice.database}.{table_slice.schema}"
        )
        tables = cursor.fetchall()

    return len(tables) > 0


class SnowflakePolarsTypeHandler(DbTypeHandler[pl.DataFrame]):
    """Plugin for the Snowflake I/O Manager that can store and load Polars DataFrames as Snowflake tables.

    This handler uses Polars' native write_database method with ADBC (Arrow Database Connectivity)
    for efficient data transfer without converting to pandas.

    Examples:
        .. code-block:: python

            from dagster_snowflake import SnowflakeIOManager
            from dagster_snowflake_polars import SnowflakePolarsTypeHandler
            from dagster import Definitions, EnvVar

            class MySnowflakeIOManager(SnowflakeIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [SnowflakePolarsTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MySnowflakeIOManager(database="MY_DATABASE", account=EnvVar("SNOWFLAKE_ACCOUNT"), ...)
                }
            )
    """

    def handle_output(
        self, context: OutputContext, table_slice: TableSlice, obj: pl.DataFrame, connection
    ) -> Mapping[str, RawMetadataValue]:
        # Rename columns to uppercase to match Snowflake convention
        with_uppercase_cols = obj.rename({col: col.upper() for col in obj.columns})
        write_mode = "replace"

        # Use the fully qualified table name
        full_table_name = f"{table_slice.database.upper()}.{table_slice.schema.upper()}.{table_slice.table.upper()}"  # pyright: ignore[reportOptionalMemberAccess]

        # If we're appending to a partition, we need to delete existing data for that partition first
        # Determine the write mode based on whether we're dealing with partitions
        # For partitioned assets, we should append rather than replace
        if table_slice.partition_dimensions and _table_exists(table_slice, connection):
            write_mode = "append"
            # Build DELETE statement for the partition
            delete_stmt = f"DELETE FROM {full_table_name} WHERE "
            partition_conditions = []
            for dim in table_slice.partition_dimensions:
                partition_conditions.append(f"{dim.partition_expr} = '{dim.partitions[0]}'")
            delete_stmt += " AND ".join(partition_conditions)
            connection.cursor().execute(delete_stmt)

        # Write using Polars native write_database with ADBC
        # This is more efficient than converting to pandas

        with connection.cursor() as cursor:
            cursor.execute(f"USE DATABASE {table_slice.database.upper()}")  # pyright: ignore[reportOptionalMemberAccess]
            cursor.execute(f"USE SCHEMA {table_slice.schema.upper()}")

        with_uppercase_cols.write_database(
            table_name=table_slice.table.upper(),
            connection=connection,
            if_table_exists=write_mode,
            engine="adbc",
        )

        return {
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
                        TableColumn(name=str(name), type=str(dtype))
                        for name, dtype in zip(obj.columns, obj.dtypes)
                    ]
                )
            ),
        }

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection
    ) -> pl.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pl.DataFrame()

        # Use Snowflake cursor to fetch data
        cursor = connection.cursor()
        cursor.execute(SnowflakeDbClient.get_select_statement(table_slice))

        # Fetch all data and column names
        data = cursor.fetchall()
        columns = [desc[0].lower() for desc in cursor.description]

        # Create Polars DataFrame from the fetched data
        if data:
            result = pl.DataFrame(data, schema=columns, orient="row")
        else:
            result = pl.DataFrame(schema=[(col, pl.Utf8) for col in columns])

        return result

    @property
    def supported_types(self):
        return [pl.DataFrame]


class SnowflakePolarsIOManager(SnowflakeIOManager):
    """An I/O manager definition that reads inputs from and writes Polars DataFrames to Snowflake. When
    using the SnowflakePolarsIOManager, any inputs and outputs without type annotations will be loaded
    as Polars DataFrames.


    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_snowflake_polars import SnowflakePolarsIOManager
            from dagster import asset, Definitions, EnvVar
            import polars as pl

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": SnowflakePolarsIOManager(database="MY_DATABASE", account=EnvVar("SNOWFLAKE_ACCOUNT"), ...)
                }
            )

        You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": SnowflakePolarsIOManager(database="my_database", schema="my_schema", ...)
                }
            )


        On individual assets, you can also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pl.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
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
        return False

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [SnowflakePolarsTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pl.DataFrame

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=SnowflakeAdbcClient(),
            io_manager_name="SnowflakePolarsIOManager",
            database=self.database,
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
        )


@io_manager(config_schema=SnowflakePolarsIOManager.to_config_schema())
def snowflake_polars_io_manager(init_context):
    """An I/O manager definition that reads inputs from and writes Polars DataFrames to Snowflake. When
    using the snowflake_polars_io_manager, any inputs and outputs without type annotations will be loaded
    as Polars DataFrames.


    Returns:
        IOManagerDefinition

    Examples:

        .. code-block:: python

            from dagster_snowflake_polars import snowflake_polars_io_manager
            from dagster import asset, Definitions
            import polars as pl

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pl.DataFrame:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={
                    "io_manager": snowflake_polars_io_manager.configured({
                        "database": "my_database",
                        "account" : {"env": "SNOWFLAKE_ACCOUNT"},
                        ...
                    })
                }
            )

        You can set a default schema to store the assets using the ``schema`` configuration value of the Snowflake I/O
        Manager. This schema will be used if no other schema is specified directly on an asset or op.

        .. code-block:: python

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": snowflake_polars_io_manager.configured(
                    {"database": "my_database", "schema": "my_schema", ...} # will be used as the schema
                )}
            )


        On individual assets, you an also specify the schema where they should be stored using metadata or
        by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata are defined, the metadata will
        take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in snowflake
            )
            def my_table() -> pl.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in snowflake
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
    return DbIOManager(
        type_handlers=[SnowflakePolarsTypeHandler()],
        db_client=SnowflakeAdbcClient(),
        io_manager_name="SnowflakePolarsIOManager",
        database=init_context.resource_config["database"],
        schema=init_context.resource_config.get("schema"),
        default_load_type=pl.DataFrame,
    )
