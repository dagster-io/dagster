from abc import abstractmethod
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, cast

import sqlalchemy
from dagster import (
    InputContext,
    IOManagerDefinition,
    OutputContext,
    _check as check,
    io_manager,
)
from dagster._config.pythonic_config import ConfigurableIOManagerFactory
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbClient,
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
    static_where_clause,
)
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from pydantic import Field
from sqlalchemy.engine import Connection

from dagster_postgres.utils import create_pg_connection, create_pg_engine, get_conn_string

# ``%z`` keeps the UTC offset of timezone-aware partition bounds so that comparisons against
# ``timestamptz`` columns do not depend on the session time zone. It renders as an empty string
# for naive datetimes, and PostgreSQL ignores the offset when casting to ``timestamp``.
POSTGRES_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"


def quote_identifier(name: str) -> str:
    """Quotes a PostgreSQL identifier so that case and special characters are preserved.

    Pandas ``to_sql`` quotes the schema, table and column names it creates, so every statement
    the I/O manager issues must quote identifiers the same way to address the same objects.
    """
    return '"' + name.replace('"', '""') + '"'


def format_postgres_table_fqn(table_slice: TableSlice) -> str:
    """Returns the quoted ``"schema"."table"`` name for a table slice."""
    return f"{quote_identifier(table_slice.schema)}.{quote_identifier(table_slice.table)}"


def postgres_url_from_resource_config(resource_config: Any) -> str:
    """Builds a SQLAlchemy URL from the resource config of a Postgres I/O manager.

    The config must contain either ``postgres_url`` or the ``hostname``/``username`` connection
    parts, mirroring the ``postgres_url`` / ``postgres_db`` choice offered by the storage classes
    in this package.
    """
    config = resource_config or {}
    postgres_url = config.get("postgres_url")
    if postgres_url:
        return postgres_url

    hostname = config.get("hostname")
    username = config.get("username")
    check.invariant(
        hostname and username,
        "Postgres I/O manager config must contain either `postgres_url` or `hostname` and"
        " `username` (plus optional `password`, `db_name`, `port` and `params`).",
    )
    return get_conn_string(
        username=cast("str", username),
        password=config.get("password") or "",
        hostname=cast("str", hostname),
        db_name=config.get("db_name") or "",
        port=str(config.get("port") or 5432),
        params=config.get("params") or None,
        scheme=config.get("scheme") or "postgresql",
    )


def build_postgres_io_manager(
    type_handlers: Sequence[DbTypeHandler], default_load_type: type | None = None
) -> IOManagerDefinition:
    """Builds an I/O manager definition that reads inputs from and writes outputs to PostgreSQL.

    Args:
        type_handlers (Sequence[DbTypeHandler]): Each handler defines how to translate between
            PostgreSQL tables and an in-memory type - e.g. a Pandas DataFrame. If only
            one DbTypeHandler is provided, it will be used as the default_load_type.
        default_load_type (Type): When an input has no type annotation, load it as this type.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_postgres import build_postgres_io_manager
            from dagster_postgres_pandas import PostgresPandasTypeHandler

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in postgres
            )
            def my_table() -> pd.DataFrame:  # the name of the asset will be the table name
                ...

            postgres_io_manager = build_postgres_io_manager([PostgresPandasTypeHandler()])

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": postgres_io_manager.configured(
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
                "io_manager": postgres_io_manager.configured(
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
        def my_table_a(my_table: pd.DataFrame):
            # my_table will just contain the data from column "a"
            ...

    """

    @dagster_maintained_io_manager
    @io_manager(config_schema=PostgresIOManager.to_config_schema())
    def postgres_io_manager(init_context):
        """I/O Manager for storing outputs in a PostgreSQL database.

        Assets will be stored in the schema and table name specified by their AssetKey.
        Subsequent materializations of an asset will overwrite previous materializations of that
        asset. Op outputs will be stored in the schema specified by output metadata (defaults to
        public) in a table of the name of the output.
        """
        return DbIOManager(
            type_handlers=type_handlers,
            db_client=PostgresDbClient(),
            io_manager_name="PostgresIOManager",
            database=init_context.resource_config.get("db_name") or "",
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return postgres_io_manager


class PostgresIOManager(ConfigurableIOManagerFactory):
    """Base class for an I/O manager definition that reads inputs from and writes outputs to
    PostgreSQL.

    The connection can be configured either with a full ``postgres_url`` or with the individual
    ``hostname``, ``username``, ``password``, ``db_name``, ``port`` and ``params`` values.

    Examples:
        .. code-block:: python

            from dagster_postgres import PostgresIOManager
            from dagster_postgres_pandas import PostgresPandasTypeHandler
            from dagster import Definitions, EnvVar

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

        You can set a default schema to store the assets using the ``schema`` configuration value
        of the Postgres I/O Manager. This schema will be used if no other schema is specified
        directly on an asset or op.

        .. code-block:: python

            Definitions(
                assets=[my_table],
                resources={
                    "io_manager": MyPostgresIOManager(
                        hostname="localhost",
                        username="postgres",
                        password=EnvVar("PG_PASSWORD"),
                        db_name="analytics",
                        schema="my_schema",
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
            def my_table_a(my_table: pd.DataFrame):
                # my_table will just contain the data from column "a"
                ...

    """

    postgres_url: str | None = Field(
        default=None,
        description=(
            "Full SQLAlchemy connection URL, e.g. postgresql://user:pass@host:5432/db. Takes"
            " precedence over the individual connection fields when set."
        ),
    )
    hostname: str | None = Field(default=None, description="PostgreSQL server host name.")
    username: str | None = Field(default=None, description="PostgreSQL user name.")
    password: str | None = Field(default=None, description="PostgreSQL password.")
    db_name: str | None = Field(default=None, description="Name of the database to connect to.")
    port: int = Field(default=5432, description="PostgreSQL server port.")
    params: dict[str, Any] = Field(
        default={},
        description=(
            "Additional query parameters appended to the connection URL, e.g."
            " {'sslmode': 'require'}."
        ),
    )
    scheme: str = Field(
        default="postgresql",
        description="URL scheme used when building the connection URL from the individual fields.",
    )
    schema_: str | None = Field(
        default=None, alias="schema", description="Name of the schema to use."
    )  # schema is a reserved word for pydantic

    @staticmethod
    @abstractmethod
    def type_handlers() -> Sequence[DbTypeHandler]: ...

    @staticmethod
    def default_load_type() -> type | None:
        return None

    def create_io_manager(self, context) -> DbIOManager:
        return DbIOManager(
            db_client=PostgresDbClient(),
            database=self.db_name or "",
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
            io_manager_name="PostgresIOManager",
        )


class PostgresDbClient(DbClient[Connection]):
    @staticmethod
    def get_table_name(table_slice: TableSlice) -> str:
        return f"{table_slice.schema}.{table_slice.table}"

    @staticmethod
    def delete_table_slice(
        context: OutputContext, table_slice: TableSlice, connection: Connection
    ) -> None:
        # Postgres aborts the whole transaction when a statement fails, so instead of catching an
        # "undefined table" error we check for the table first.
        exists = connection.execute(
            sqlalchemy.text("SELECT to_regclass(:fqn)"),
            {"fqn": format_postgres_table_fqn(table_slice)},
        ).scalar()
        if exists is None:
            return
        # The cleanup statement embeds partition keys as quoted literals, so it is sent to the
        # driver as-is without parameters: ``sqlalchemy.text`` would treat a key such as ``:foo``
        # as a bind parameter. The DBAPI cursor shares this connection's open transaction.
        cursor = connection.connection.cursor()
        try:
            cursor.execute(_get_cleanup_statement(table_slice))
        finally:
            cursor.close()

    @staticmethod
    def ensure_schema_exists(
        context: OutputContext, table_slice: TableSlice, connection: Connection
    ) -> None:
        connection.execute(
            sqlalchemy.text(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(table_slice.schema)}")
        )

    @staticmethod
    def get_select_statement(table_slice: TableSlice) -> str:
        col_str = (
            ", ".join(quote_identifier(col) for col in table_slice.columns)
            if table_slice.columns
            else "*"
        )
        fqn = format_postgres_table_fqn(table_slice)
        if table_slice.partition_dimensions:
            query = f"SELECT {col_str} FROM {fqn} WHERE\n"
            return query + _partition_where_clause(table_slice.partition_dimensions)
        else:
            return f"SELECT {col_str} FROM {fqn}"

    @staticmethod
    @contextmanager
    def connect(
        context: InputContext | OutputContext, table_slice: TableSlice
    ) -> Iterator[Connection]:
        engine = create_pg_engine(postgres_url_from_resource_config(context.resource_config))
        try:
            with create_pg_connection(engine) as conn:
                # All statements issued while handling an output (schema creation, cleanup and the
                # insert itself) are committed together, so a failed write leaves the previous
                # materialization in place.
                with conn.begin():
                    yield conn
        finally:
            engine.dispose()


def _get_cleanup_statement(table_slice: TableSlice) -> str:
    """Returns a SQL statement that deletes data in the given table to make way for the output data
    being written.
    """
    fqn = format_postgres_table_fqn(table_slice)
    if table_slice.partition_dimensions:
        query = f"DELETE FROM {fqn} WHERE\n"
        return query + _partition_where_clause(table_slice.partition_dimensions)
    else:
        return f"DELETE FROM {fqn}"


def _partition_where_clause(partition_dimensions: Sequence[TablePartitionDimension]) -> str:
    return " AND\n".join(
        (
            _time_window_where_clause(partition_dimension)
            if isinstance(partition_dimension.partitions, TimeWindow)
            else static_where_clause(partition_dimension)
        )
        for partition_dimension in partition_dimensions
    )


def _time_window_where_clause(table_partition: TablePartitionDimension) -> str:
    partition = cast("TimeWindow", table_partition.partitions)
    start_dt, end_dt = partition
    start_dt_str = start_dt.strftime(POSTGRES_DATETIME_FORMAT)
    end_dt_str = end_dt.strftime(POSTGRES_DATETIME_FORMAT)
    return f"""{table_partition.partition_expr} >= '{start_dt_str}' AND {table_partition.partition_expr} < '{end_dt_str}'"""
