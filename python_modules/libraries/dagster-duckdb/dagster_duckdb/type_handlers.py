from pathlib import Path
from typing import Union, cast

import duckdb

from dagster import InputContext, OutputContext
from dagster import _check as check

from .io_manager import DbTypeHandler


class DuckDBPandasTypeHandler(DbTypeHandler):
    """Stores and loads Pandas DataFrames in DuckDB."""

    import pandas as pd

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

        context.add_output_metadata({"row_count": obj.shape[0], "path": filepath})

    def load_input(self, context: InputContext, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Loads the input as a Pandas DataFrame."""
        return conn.execute(
            f"SELECT * FROM {self._table_path(context, cast(OutputContext, context.upstream_output))}"
        ).fetchdf()

    @property
    def supported_output_types(self):
        import pandas as pd

        return [pd.DataFrame]

    @property
    def supported_input_types(self):
        import pandas as pd

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


class DuckDBParquetTypeHandler(DbTypeHandler):
    """Stores Parquet files in DuckDB.
    **Note:** This type handler can only store outputs. It cannot currently load inputs.
    """

    import pyspark

    def handle_output(
        self,
        context: OutputContext,
        obj: pyspark.sql.DataFrame,
        conn: duckdb.DuckDBPyConnection,
        base_path: str,
    ):
        """Stores the given object at the provided filepath."""
        filepath = self._get_path(context)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        row_count = obj.count()
        obj.write.parquet(path=filepath, mode="overwrite")

        if context.has_asset_partitions:
            to_scan = Path(filepath.parent, "*.pq", "*.parquet")
        else:
            to_scan = filepath
        conn.execute(f"create schema if not exists {self._schema(context)};")
        conn.execute(
            f"create or replace view {self._table_path(context)} as "
            f"select * from parquet_scan('{to_scan}');"
        )

        context.add_output_metadata({"row_count": row_count, "path": filepath})

    def load_input(
        self, context: InputContext, conn: duckdb.DuckDBPyConnection
    ) -> Union[pyspark.sql.DataFrame, str]:
        """Loads the return of the query as the correct type."""

        check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input."
        )

    def _get_path(self, context: OutputContext, base_path: str):
        key = context.asset_key.path[-1]  # type: ignore

        if context.has_asset_partitions:
            start, end = context.asset_partitions_time_window
            dt_format = "%Y%m%d%H%M%S"
            partition_str = start.strftime(dt_format) + "_" + end.strftime(dt_format)
            return Path(base_path, key, f"{partition_str}.pq")
        else:
            return Path(base_path, f"{key}.pq")

    @property
    def supported_output_types(self):
        import pyspark

        return [pyspark.sql.DataFrame]

    @property
    def supported_input_types(self):
        return []
