from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

import dagster as dg
import duckdb
import pandas as pd


class DuckDBPandasIOManager(dg.ConfigurableIOManager):
    database: str
    db_schema: str = "main"
    retry_attempts: int = 10
    retry_delay_seconds: float = 0.2

    def handle_output(self, context: dg.OutputContext, obj: object) -> None:
        if not isinstance(obj, pd.DataFrame):
            raise TypeError(
                f"DuckDBPandasIOManager only supports pandas DataFrames, got {type(obj)!r}."
            )

        table_name = _table_name_for_key(context.asset_key)

        def _write_output() -> None:
            with duckdb.connect(self.database) as connection:
                connection.execute(f"create schema if not exists {self.db_schema}")
                connection.register("asset_df", obj)
                connection.execute(
                    f"create or replace table {self.db_schema}.{table_name} as "
                    "select * from asset_df"
                )

        self._with_retry(_write_output, action=f"write table {self.db_schema}.{table_name}")

        context.add_output_metadata(
            {
                "database": self.database,
                "schema": self.db_schema,
                "table": table_name,
                "rows": len(obj),
            }
        )

    def load_input(self, context: dg.InputContext) -> pd.DataFrame:
        table_name = _table_name_for_key(context.asset_key)
        return self._with_retry(
            lambda: self._load_table(table_name),
            action=f"read table {self.db_schema}.{table_name}",
        )

    def _load_table(self, table_name: str) -> pd.DataFrame:
        with duckdb.connect(self.database) as connection:
            return connection.execute(f"select * from {self.db_schema}.{table_name}").fetch_df()

    def _with_retry(self, fn: Callable, *, action: str):
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return fn()
            except duckdb.IOException as exc:
                if "Conflicting lock is held" not in str(exc):
                    raise
                last_error = exc
                if attempt == self.retry_attempts:
                    break
                time.sleep(self.retry_delay_seconds)

        assert last_error is not None
        raise last_error


def _table_name_for_key(asset_key: dg.AssetKey) -> str:
    return "__".join(asset_key.path)


def make_duckdb_io_manager(
    tenant_name: str,
    *,
    base_dir: str | Path | None = None,
) -> DuckDBPandasIOManager:
    """Create a per-tenant DuckDB IO manager."""
    root_dir = Path(base_dir) if base_dir is not None else Path("data")
    root_dir.mkdir(parents=True, exist_ok=True)
    database_path = root_dir / f"{tenant_name}.duckdb"
    return DuckDBPandasIOManager(database=str(database_path))
