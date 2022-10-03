from pathlib import Path
from typing import cast

import duckdb
import pandas as pd

from dagster import Field, IOManager, InputContext, OutputContext
from dagster import _check as check
from dagster import io_manager
from dagster._seven.temp_dir import get_system_temp_directory
from dagster._utils.backoff import backoff


class DuckDBCSVIOManager(IOManager):
    """Stores data in csv files and creates duckdb views over those files."""

    def __init__(self, base_path):
        self._base_path = base_path

    def handle_output(self, context: OutputContext, obj: object):
        if obj is not None:  # if this is a dbt output, then the value will be None
            if not isinstance(obj, pd.DataFrame):
                check.failed(f"Outputs of type {type(obj)} not supported.")

            con = self._connect_duckdb(context).cursor()
            filepath = self._get_path(context)
            # ensure path exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            # write df to csv file
            obj.to_csv(filepath)

            # create view over that file
            con.execute(f"create schema if not exists {self._schema(context, context)};")
            con.execute(
                f"create or replace view {self._table_path(context, context)} as "
                f"select * from '{filepath}';"
            )
            con.close()

    def load_input(self, context: InputContext):
        check.invariant(not context.has_asset_partitions, "Can't load partitioned inputs")

        if context.dagster_type.typing_type == pd.DataFrame:
            con = self._connect_duckdb(context).cursor()
            ret = con.execute(
                f"SELECT * FROM {self._table_path(context, cast(OutputContext, context.upstream_output))}"
            ).fetchdf()
            con.close()
            return ret

        check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input either on the argument of the @asset-decorated function."
        )

    def _get_path(self, context: OutputContext) -> Path:
        if context.has_asset_key:
            return Path(f"{self._base_path}/{'_'.join(context.asset_key.path)}.csv")
        else:
            keys = context.get_identifier()
            run_id = keys[0]
            output_identifiers = keys[1:]  # variable length because of mapping key

            path = ["storage", run_id, "files", *output_identifiers]
        return Path(f"{self._base_path}/{'_'.join(path)}.csv")

    def _schema(self, context, output_context: OutputContext):
        if context.has_asset_key:
            # the schema is the second to last component of the asset key, e.g.
            # AssetKey([database, schema, tablename])
            return context.asset_key.path[-2]
        else:
            # for non-asset outputs, the schema should be specified as metadata, or will default to public
            context_metadata = output_context.metadata or {}
            return context_metadata.get("schema", "public")

    def _table(self, context, output_context: OutputContext):
        if context.has_asset_key:
            # the table is the  last component of the asset key, e.g.
            # AssetKey([database, schema, tablename])
            return context.asset_key.path[-1]
        else:
            # for non-asset outputs, the table is the output name
            return output_context.name

    def _table_path(self, context, output_context: OutputContext):
        return f"{self._schema(context, output_context)}.{self._table(context, output_context)}"

    def _connect_duckdb(self, context):
        return backoff(
            fn=duckdb.connect,
            retry_on=(RuntimeError,),
            kwargs={"database": context.resource_config["duckdb_path"], "read_only": False},
        )


@io_manager(config_schema={"base_path": Field(str, is_required=False), "duckdb_path": str})
def duckdb_io_manager(init_context):
    """IO Manager for storing outputs in a DuckDB database

    Supports storing and loading Pandas DataFrame objects. Converts the DataFrames to CSV and
    creates DuckDB views over the files.

    Assets will be stored in the schema and table name specified by their AssetKey.
    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    Op outputs will be stored in the schema specified by output metadata (defaults to public) in a
    table of the name of the output.
    """
    return DuckDBCSVIOManager(
        base_path=init_context.resource_config.get("base_path", get_system_temp_directory())
    )
