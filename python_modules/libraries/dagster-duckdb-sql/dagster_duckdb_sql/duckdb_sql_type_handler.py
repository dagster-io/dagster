from typing import Any, Mapping, Optional, Sequence, Type

from dagster import InputContext, MarkdownMetadataValue, OutputContext
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster._core.storage.sql import SqlQuery
from dagster_duckdb.io_manager import (
    DuckDbClient,
    DuckDBIOManager,
    build_duckdb_io_manager,
)
from duckdb import DuckDBPyConnection


class DuckDBSqlTypeHandler(DbTypeHandler[SqlQuery]):
    """Posts SQL queries to DuckDB and constructs SQL queries.
    Uses INSERT INTO statements and SELECT statements.

    To use this type handler, return it from the ``type_handlers` method of an I/O manager that inherits from ``DuckDBIOManager``.

    Example:
        .. code-block:: python

            from dagster_duckdb import DuckDBIOManager
            from dagster_duckdb_sql import DuckDBSqlTypeHandler
            from dagster._core.storage.sql import SqlQuery

            class MyDuckDBIOManager(DuckDBIOManager):
                @staticmethod
                def type_handlers() -> Sequence[DbTypeHandler]:
                    return [DuckDBSqlTypeHandler()]

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in duckdb
            )
            def my_table() -> SqlQuery:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": MyDuckDBIOManager(database="my_db.duckdb")}
            )

    """

    @staticmethod
    def _schemas_are_compatible(table_name, query_str, connection):
        """Check that the incoming schema is equal to the existing schema.
        """
        existing_schema = connection.execute(f"SELECT * FROM {table_name} LIMIT 0").description
        query_schema = connection.execute(f"{query_str} LIMIT 0").description

        insert_fields = {field[0]: field[1] for field in existing_schema}
        dest_fields = {field[0]: field[1] for field in query_schema}

        if insert_fields == dest_fields:
            return True

        raise ValueError(
            f"Schemas do not match. "
            f"Incoming: {insert_fields}. "
            f"Existing: {dest_fields}"
        )

    def _insert_query(
        self,
        query: SqlQuery,
        table_slice: TableSlice,
        connection: DuckDBPyConnection
    ) -> None:
        """Create and execute an insert values query from the parsed query.
        """
        query_str = query.parse_bindings()
        table_name = f"{table_slice.schema}.{table_slice.table}"

        connection.execute(
            f"create table if not exists {table_slice.schema}.{table_slice.table} as ({query_str})"
        )

        if not connection.fetchall():
            # Table exists, so check the schemas match
            # Then insert the data
            if self._schemas_are_compatible(table_name, query_str, connection):
                insert_query = (f"INSERT INTO {table_name} ({query_str})")
                connection.execute(insert_query)

    @staticmethod
    def _get_metadata(
        query: SqlQuery,
        table_slice: TableSlice,
        connection: DuckDBPyConnection
    ) -> Mapping[str, Any]:
        """Get metadata from a table.
        """
        query_str = query.parse_bindings()
        row_count = connection.execute(
            f"SELECT COUNT(*) FROM ({query_str});"
        ).fetchall()[0][0]

        schema_df = connection.execute(
            f"SELECT * FROM information_schema.columns"
            f" WHERE table_schema = '{table_slice.schema}'"
            f" AND table_name = '{table_slice.table}'"
        ).fetchdf()

        return {
            "row_count": row_count,
            "col_count": schema_df.shape[0],
            "schema": MarkdownMetadataValue(schema_df[["column_name", "data_type"]].to_markdown())
        }

    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: SqlQuery,
        connection: DuckDBPyConnection
    ) -> None:
        """Parses the SQL query and runs it in duckdb to insert records into the table."""
        self._insert_query(obj, table_slice, connection)
        metadata = self._get_metadata(obj, table_slice, connection)
        context.add_output_metadata(metadata)

    def load_input(
        self, context: InputContext, table_slice: TableSlice, connection: DuckDBPyConnection
    ) -> SqlQuery:
        """Constructs the SQL query required to select the asset from duckdb."""
        query_str = DuckDbClient.get_select_statement(table_slice)
        return SqlQuery(query_str)

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [SqlQuery]


duckdb_sql_io_manager = build_duckdb_io_manager(
    [DuckDBSqlTypeHandler()], default_load_type=SqlQuery
)
duckdb_sql_io_manager.__doc__ = """
An I/O manager definition that posts SQL queries to DuckDB and constructs SQL queries. When
using the duckdb_sql_io_manager, any inputs and outputs without type annotations will be loaded
as SqlQuerys.

Returns:
    IOManagerDefinition

Examples:

    .. code-block:: python

        from dagster_duckdb_sql import duckdb_sql_io_manager
        from dagster._core.storage.sql import SqlQuery

        @asset(
            key_prefix=["my_schema"]  # will be used as the schema in DuckDB
        )
        def my_table() -> SqlQuery:  # the name of the asset will be the table name
            ...

        @repository
        def my_repo():
            return with_resources(
                [my_table],
                {"io_manager": duckdb_sql_io_manager.configured({"database": "my_db.duckdb"})}
            )

    If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
    the I/O Manager. For assets, the schema will be determined from the asset key.
    For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
    via config or on the asset/op, "public" will be used for the schema.

    .. code-block:: python

        @op(
            out={"my_table": Out(metadata={"schema": "my_schema"})}
        )
        def make_my_table() -> SqlQuery:
            # the returned query will be inserted into my_schema.my_table
            ...

    To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
    In or AssetIn.

    .. code-block:: python

        @asset(
            ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
        )
        def my_table_a(my_table: SqlQuery) -> SqlQuery:
            # my_table will just contain the data from column "a"
            ...

"""


class DuckDBSqlIOManager(DuckDBIOManager):
    """An I/O manager definition that posts SQL queries to DuckDB and constructs SQL queries. When
    using the duckdb_sql_io_manager, any inputs and outputs without type annotations will be loaded
    as SqlQuerys.

    Returns:
        IOManagerDefinition

    Examples:
        .. code-block:: python

            from dagster_duckdb_sql import DuckDBSqlIOManager
            from dagster._core.storage.sql import SqlQuery

            @asset(
                key_prefix=["my_schema"]  # will be used as the schema in DuckDB
            )
            def my_table() -> SqlQuery:  # the name of the asset will be the table name
                ...

            defs = Definitions(
                assets=[my_table],
                resources={"io_manager": DuckDBSqlIOManager(database="my_db.duckdb")}
            )

        If you do not provide a schema, Dagster will determine a schema based on the assets and ops using
        the I/O Manager. For assets, the schema will be determined from the asset key, as in the above example.
        For ops, the schema can be specified by including a "schema" entry in output metadata. If "schema" is not provided
        via config or on the asset/op, "public" will be used for the schema.

        .. code-block:: python

            @op(
                out={"my_table": Out(metadata={"schema": "my_schema"})}
            )
            def make_my_table() -> SqlQuery:
                # the returned value will be stored at my_schema.my_table
                ...

        To only use specific columns of a table as input to a downstream op or asset, add the metadata "columns" to the
        In or AssetIn.

        .. code-block:: python

            @asset(
                ins={"my_table": AssetIn("my_table", metadata={"columns": ["a"]})}
            )
            def my_table_a(my_table: SqlQuery) -> SqlQuery:
                # my_table will just contain the data from column "a"
                ...

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DuckDBSqlTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return SqlQuery
