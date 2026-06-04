"""Lightweight stand-in for the `dagster_duckdb` integration package.

The real `dagster-duckdb` library was removed as part of the lightweight-dagster
effort (it lived under python_modules/libraries/). This shim provides the small
public surface the dagster_essentials course uses — `DuckDBResource` with a
`database` field and a `get_connection()` context manager — built on the stdlib
`ConfigurableResource` base plus the `duckdb` engine. No other dagster deps.
"""

from contextlib import contextmanager

import duckdb
from dagster import ConfigurableResource


class DuckDBResource(ConfigurableResource):
    """Minimal DuckDB resource compatible with the course's usage.

    Mirrors dagster_duckdb.DuckDBResource for the subset the course exercises:
        with database.get_connection() as conn:
            conn.execute(query)
    """

    database: str
    connection_config: dict = {}

    @contextmanager
    def get_connection(self):
        conn = duckdb.connect(self.database, config=self.connection_config or {})
        try:
            yield conn
        finally:
            conn.close()


__all__ = ["DuckDBResource"]
