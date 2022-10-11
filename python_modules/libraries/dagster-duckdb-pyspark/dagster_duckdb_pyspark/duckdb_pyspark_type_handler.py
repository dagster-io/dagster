from pathlib import Path

import duckdb
import pyspark
from dagster_duckdb import DbTypeHandler

from dagster import InputContext, OutputContext
from dagster import _check as check


class DuckDBPySparkTypeHandler(DbTypeHandler[pyspark.sql.DataFrame]):
    """Stores PySpark DataFrames in DuckDB.

    **Note:** This type handler can only store outputs. It cannot currently load inputs.

    To use this type handler, pass it to ``build_duckdb_io_manager``

    Example:
        .. code-block:: python

            from dagster_duckdb import build_duckdb_io_manager
            from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler

            duckdb_io_manager = build_duckdb_io_manager([DuckDBPySparkTypeHandler()])

            @job(resource_defs={'io_manager': duckdb_io_manager})
            def my_job():
                ...
    """

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

    def load_input(self, context: InputContext, conn: duckdb.DuckDBPyConnection):
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
        return [pyspark.sql.DataFrame]

    @property
    def supported_input_types(self):
        return []
