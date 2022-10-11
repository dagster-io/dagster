from pathlib import Path
from typing import cast

import duckdb
import pandas as pd
from dagster_duckdb import DbTypeHandler

from dagster import InputContext, OutputContext
from dagster import _check as check


class DuckDBPandasTypeHandler(DbTypeHandler[pd.DataFrame]):
    """Stores and loads Pandas DataFrames in DuckDB.

    To use this type handler, pass it to ``build_duckdb_io_manager``

    Example:
        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pandas import DuckDBPandasTypeHandler

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

            @job(resource_defs={'io_manager': duckdb_io_manager})
            def my_job():
                ...

    """

    def handle_output(
        self,
        context: OutputContext,
        obj: pd.DataFrame,
        conn: duckdb.DuckDBPyConnection,
        base_path: str,
    ):
        """Stores the pandas DataFrame as a csv and loads it as a view in duckdb."""
        check.invariant(
            not context.has_asset_partitions,
            "DuckDBPandasTypeHadnler Can't store partitioned outputs",
        )

        filepath = self._get_path(context, base_path)
        # ensure path exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        obj.to_csv(filepath)

        conn.execute(f"create schema if not exists {self._schema(context, context)};")
        conn.execute(
            f"create or replace view {self._table_path(context, context)} as "
            f"select * from '{filepath}';"
        )

        context.add_output_metadata({"row_count": obj.shape[0], "path": str(filepath)})

    def load_input(self, context: InputContext, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        return conn.execute(
            f"SELECT * FROM {self._table_path(context, cast(OutputContext, context.upstream_output))}"
        ).fetchdf()

    @property
    def supported_output_types(self):
        return [pd.DataFrame]

    @property
    def supported_input_types(self):
        return [pd.DataFrame]

    def _get_path(self, context: OutputContext, base_path: str) -> Path:
        if context.has_asset_key:
            return Path(f"{base_path}/{'_'.join(context.asset_key.path)}.csv")
        else:
            keys = context.get_identifier()
            run_id = keys[0]
            output_identifiers = keys[1:]  # variable length because of mapping key

            path = ["storage", run_id, "files", *output_identifiers]
        return Path(f"{base_path}/{'_'.join(path)}.csv")
