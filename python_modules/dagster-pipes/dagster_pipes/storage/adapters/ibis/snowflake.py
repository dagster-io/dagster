from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional

import ibis
import sqlglot
from ibis.backends.snowflake import Backend as SnowflakeBackend

from dagster_pipes.storage.adapters.ibis.base import IbisTableAdapter, PartitionRange
from dagster_pipes.storage.partitions import PartitionKeyRange, TimeWindowRange
from dagster_pipes.storage.types import StorageAddress

# Transaction control SQL (generated via sqlglot for consistency)
_BEGIN = sqlglot.exp.Transaction().sql(dialect="snowflake")
_COMMIT = sqlglot.exp.Commit().sql(dialect="snowflake")
_ROLLBACK = sqlglot.exp.Rollback().sql(dialect="snowflake")


@contextmanager
def snowflake_transaction(conn: SnowflakeBackend) -> Iterator[None]:
    """Context manager for Snowflake transactions."""
    conn.raw_sql(_BEGIN)
    try:
        yield
        conn.raw_sql(_COMMIT)
    except Exception:
        conn.raw_sql(_ROLLBACK)
        raise


class SnowflakeStorageAdapter(IbisTableAdapter[SnowflakeBackend]):
    def __init__(
        self,
        user: str,
        account: str,
        database: str,
        schema: Optional[str] = None,
        password: Optional[str] = None,
        warehouse: Optional[str] = None,
        role: Optional[str] = None,
        authenticator: Optional[str] = None,
        private_key: Optional[bytes] = None,
        **extra_conn_args: Any,
    ):
        """Initialize the Snowflake adapter.

        Args:
            user: Snowflake username.
            account: Snowflake account identifier (org_id-account_id format).
            database: Default database name.
            schema: Default schema name.
            password: Password for authentication.
            warehouse: Default warehouse to use.
            role: Default role to use.
            authenticator: Authentication method (e.g., "externalbrowser" for SSO).
            private_key: Private key bytes for key-pair authentication.
            **extra_conn_args: Additional connection arguments passed to ibis.snowflake.connect().
        """
        self._database = database
        self._schema = schema

        conn_args: dict[str, Any] = {
            "user": user,
            "account": account,
            "database": database,
        }
        if schema is not None:
            conn_args["schema"] = schema
        if password is not None:
            conn_args["password"] = password
        if warehouse is not None:
            conn_args["warehouse"] = warehouse
        if role is not None:
            conn_args["role"] = role
        if authenticator is not None:
            conn_args["authenticator"] = authenticator
        if private_key is not None:
            conn_args["private_key"] = private_key
        conn_args.update(extra_conn_args)

        super().__init__(backend_type=SnowflakeBackend, **conn_args)

    @property
    def storage_type(self) -> str:
        return "snowflake"

    def matches_address(self, addr: StorageAddress) -> bool:
        if addr.storage_type != self.storage_type:
            return False

        # Parse address: could be "table", "schema.table", or "database.schema.table"
        parts = addr.address.split(".")
        if len(parts) == 3:
            # database.schema.table - check database matches
            return parts[0] == self._database
        elif len(parts) == 2:
            # schema.table - check schema matches if we have one configured
            if self._schema is not None:
                return parts[0] == self._schema
            return True
        else:
            # Just table name
            return True

    def get_table_name(self, addr: StorageAddress) -> str:
        return addr.address.split(".")[-1]

    # =========================================================================
    # Snowflake-optimized upsert using DELETE + INSERT
    # =========================================================================

    def _upsert_by_partition_keys(
        self,
        conn: SnowflakeBackend,
        table_name: str,
        partition_col: str,
        keys: tuple[str, ...],
        new_data: ibis.Table,
    ) -> None:
        """Snowflake-optimized upsert using DELETE + INSERT in a transaction."""
        # Build DELETE statement with sqlglot (handles escaping)
        if len(keys) == 1:
            condition = sqlglot.condition(f'"{partition_col}" = :v', v=keys[0])
        else:
            condition = sqlglot.column(partition_col).isin(*keys)

        delete = (
            sqlglot.delete(table_name, dialect="snowflake")
            .where(condition)
            .sql(dialect="snowflake")
        )

        with snowflake_transaction(conn):
            conn.raw_sql(delete)
            conn.insert(table_name, new_data)

    def _upsert_by_partition_range(
        self,
        conn: SnowflakeBackend,
        table_name: str,
        partition_col: str,
        partition: PartitionRange,
        new_data: ibis.Table,
    ) -> None:
        """Snowflake-optimized upsert for partition ranges using DELETE + INSERT in a transaction."""
        col = sqlglot.column(partition_col)

        if isinstance(partition, PartitionKeyRange):
            # Inclusive range: >= start AND <= end
            condition = col.gte(sqlglot.exp.Literal.string(partition.start)).and_(
                col.lte(sqlglot.exp.Literal.string(partition.end))
            )
        elif isinstance(partition, TimeWindowRange):
            # Half-open range: >= start AND < end
            start_lit = sqlglot.exp.cast(
                sqlglot.exp.Literal.string(partition.start.isoformat()), "TIMESTAMP"
            )
            end_lit = sqlglot.exp.cast(
                sqlglot.exp.Literal.string(partition.end.isoformat()), "TIMESTAMP"
            )
            condition = col.gte(start_lit).and_(col.lt(end_lit))
        else:
            raise TypeError(f"Unexpected partition type: {type(partition)}")

        delete = (
            sqlglot.delete(table_name, dialect="snowflake")
            .where(condition)
            .sql(dialect="snowflake")
        )

        with snowflake_transaction(conn):
            conn.raw_sql(delete)
            conn.insert(table_name, new_data)
