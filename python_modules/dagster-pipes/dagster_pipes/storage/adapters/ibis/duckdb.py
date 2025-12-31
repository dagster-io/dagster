from collections.abc import Sequence
from typing import Any, Optional

from ibis.backends.duckdb import Backend as DuckDBBackend

from dagster_pipes.storage.adapters.ibis import IbisTableAdapter
from dagster_pipes.storage.types import StorageAddress


class DuckDBStorageAdapter(IbisTableAdapter[DuckDBBackend]):
    def __init__(
        self,
        database: str,
        read_only: bool = False,
        extensions: Optional[Sequence[str]] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        """Initialize the DuckDB adapter.

        Args:
            database: Path to the DuckDB database file, or ":memory:" for in-memory.
            read_only: Whether the database is read-only.
            extensions: A list of DuckDB extensions to install/load upon connection.
            config: DuckDB configuration parameters.
        """
        self._database = database
        conn_args: dict[str, Any] = {"database": database, "read_only": read_only}
        if extensions is not None:
            conn_args["extensions"] = extensions
        if config is not None:
            conn_args["config"] = config
        super().__init__(backend_type=DuckDBBackend, **conn_args)

    @property
    def storage_type(self) -> str:
        return "duckdb"

    def matches_address(self, addr: StorageAddress) -> bool:
        # For DuckDB, we match if the storage_type is duckdb
        # The address format is just the table name (or schema.table)
        return addr.storage_type == self.storage_type

    def get_table_name(self, addr: StorageAddress) -> str:
        # Address format: "table" or "schema.table"
        # Return the last segment as the table name
        return addr.address.split(".")[-1]
