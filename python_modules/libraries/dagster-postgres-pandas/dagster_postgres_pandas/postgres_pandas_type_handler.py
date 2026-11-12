from collections.abc import Mapping, Sequence

import pandas as pd
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.metadata import RawMetadataValue, TableMetadataSet
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_postgres.io_manager import (
    PostgresDbClient,
    PostgresIOManager,
    build_postgres_io_manager,
)
from sqlalchemy.engine import Connection


class PostgresPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Stores and loads Pandas DataFrames in PostgreSQL.

    To use this type handler, return it from the ``type_handlers`` method of an I/O manager that
    inherits from ``PostgresIOManager``.

    Example:
        .. code-block:: python

            from dagster import Definitions, EnvVar
            from dagster_postgres import PostgresIOManager
            from dagster_postgres_pandas import PostgresPandasTypeHandler

            class MyPostgresIOManager(PostgresIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [PostgresPandasTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in postgres
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MyPostgresIOManager(postgres_url=EnvVar("DAGSTER_PG_URL"))
                },
            )

    """

    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: pd.DataFrame,
        connection: Connection,
    ) -> Mapping[str, RawMetadataValue]:
        """Stores the pandas DataFrame in PostgreSQL."""
        if len(obj.columns) == 0:
            context.log.warning(
                "Skipping PostgreSQL write for DataFrame without columns. No table will be created."
            )
        else:
            # The table is created on first write and appended to afterwards; the I/O manager has
            # already deleted the rows belonging to this output (or partition) in this transaction.
            # An empty DataFrame with columns still creates the table so downstream reads succeed.
            obj.to_sql(
                name=table_slice.table,
                schema=table_slice.schema,
                con=connection,
                if_exists="append",
                index=False,
            )

        return {
            # output object may be a slice/partition, so we output different metadata keys based on
            # whether this output represents an entire table or just a slice/partition
            **(
                TableMetadataSet(partition_row_count=obj.shape[0], storage_kind="postgres")
                if context.has_partition_key
                else TableMetadataSet(row_count=obj.shape[0], storage_kind="postgres")
            ),
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=str(name), type=str(dtype))
                        for name, dtype in obj.dtypes.items()
                    ]
                )
            ),
        }

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection: Connection
    ) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            return pd.DataFrame()
        return pd.read_sql(sql=PostgresDbClient.get_select_statement(table_slice), con=connection)

    @property
    def supported_types(self):
        return [pd.DataFrame]


postgres_pandas_io_manager = build_postgres_io_manager(
    [PostgresPandasTypeHandler()], default_load_type=pd.DataFrame
)
postgres_pandas_io_manager.__doc__ = """
An I/O manager definition that reads inputs from and writes Pandas DataFrames to PostgreSQL. When
using the postgres_pandas_io_manager, any inputs and outputs without type annotations will be
loaded as Pandas DataFrames.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_postgres_pandas import postgres_pandas_io_manager

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in postgres
        )
        def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
            ...

        Definitions(
            assets=[my_table],
            resources={
                "io_manager": postgres_pandas_io_manager.configured(
                    {"postgres_url": {"env": "DAGSTER_PG_URL"}}
                )
            },
        )

    You can set a default schema to store the assets using the ``schema`` configuration value of
    the Postgres I/O Manager. This schema will be used if no other schema is specified directly on
    an asset or op.

    .. code-block:: python

        Definitions(
            assets=[my_table],
            resources={
                "io_manager": postgres_pandas_io_manager.configured(
                    {"postgres_url": {"env": "DAGSTER_PG_URL"}, "schema": "my_schema"}
                )
            },
        )

    On individual assets, you can also specify the schema where they should be stored using
    metadata or by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and metadata
    are defined, the metadata will take precedence.

    .. code-block:: python

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in postgres
        )
        def my_table() -> pd.DataFrame:
            ...

        @asset(
            metadata={"schema": "my_schema"}  # will be used as the schema in postgres
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

    To only use specific columns of a table as input to a downstream op or asset, add the metadata
    "columns" to the In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: pd.DataFrame) -> pd.DataFrame:
            # my_table will just contain the data from column "a"
            ...

"""


class PostgresPandasIOManager(PostgresIOManager):
    """An I/O manager definition that reads inputs from and writes Pandas DataFrames to PostgreSQL.
    When using the PostgresPandasIOManager, any inputs and outputs without type annotations will be
    loaded as Pandas DataFrames.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster import Definitions, EnvVar
            from dagster_postgres_pandas import PostgresPandasIOManager

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in postgres
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": PostgresPandasIOManager(postgres_url=EnvVar("DAGSTER_PG_URL"))
                },
            )

        Instead of a full URL you can pass the individual connection fields:

        .. code-block:: python

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": PostgresPandasIOManager(
                        hostname="localhost",
                        username="postgres",
                        password=EnvVar("PG_PASSWORD"),
                        db_name="analytics",
                        port=5432,
                    )
                },
            )

        You can set a default schema to store the assets using the ``schema`` configuration value
        of the Postgres I/O Manager. This schema will be used if no other schema is specified
        directly on an asset or op.

        .. code-block:: python

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": PostgresPandasIOManager(
                        postgres_url=EnvVar("DAGSTER_PG_URL"), schema="my_schema"
                    )
                },
            )

        On individual assets, you can also specify the schema where they should be stored using
        metadata or by adding a ``key_prefix`` to the asset key. If both ``key_prefix`` and
        metadata are defined, the metadata will take precedence.

        .. code-block:: python

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in postgres
            )
            def my_table() -> pd.DataFrame:
                ...

            @asset(
                metadata={"schema": "my_schema"}  # will be used as the schema in postgres
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

        To only use specific columns of a table as input to a downstream op or asset, add the
        metadata "columns" to the In or AssetIn.

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
        return [PostgresPandasTypeHandler()]

    @staticmethod
    def default_load_type() -> type | None:
        return pd.DataFrame
