from typing import Any, Optional

from ibis.backends.postgres import Backend as PostgresBackend

from dagster_pipes.storage.adapters.ibis.base import IbisTableAdapter
from dagster_pipes.storage.types import StorageAddress


class PostgresStorageAdapter(IbisTableAdapter[PostgresBackend]):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        **extra_conn_args: Any,
    ):
        """Initialize the PostgreSQL adapter.

        Args:
            host: PostgreSQL server hostname.
            port: PostgreSQL server port.
            user: PostgreSQL username.
            password: PostgreSQL password.
            database: Database name to connect to.
            schema: Default schema to use.
            **extra_conn_args: Additional connection arguments passed to ibis.postgres.connect().
        """
        self._database = database
        self._schema = schema

        conn_args: dict[str, Any] = {
            "host": host,
            "port": port,
        }
        if user is not None:
            conn_args["user"] = user
        if password is not None:
            conn_args["password"] = password
        if database is not None:
            conn_args["database"] = database
        if schema is not None:
            conn_args["schema"] = schema
        conn_args.update(extra_conn_args)

        super().__init__(backend_type=PostgresBackend, **conn_args)

    @property
    def storage_type(self) -> str:
        return "postgres"

    def matches_address(self, addr: StorageAddress) -> bool:
        if addr.storage_type != self.storage_type:
            return False

        # Parse address: could be "table" or "schema.table"
        parts = addr.address.split(".")
        if len(parts) == 2:
            # schema.table - check schema matches if we have one configured
            if self._schema is not None:
                return parts[0] == self._schema
            return True
        else:
            # Just table name
            return True

    def get_table_name(self, addr: StorageAddress) -> str:
        return addr.address.split(".")[-1]
