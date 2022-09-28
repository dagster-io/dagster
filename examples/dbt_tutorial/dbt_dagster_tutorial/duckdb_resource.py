import duckdb
import pandas as pd

from dagster import Field, IOManager
from dagster import _check as check
from dagster import io_manager
from dagster._seven.temp_dir import get_system_temp_directory


class DuckDBCSVIOManager(IOManager):
    """Stores data in csv files and creates duckdb views over those files."""

    def __init__(self, base_path):
        self._base_path = base_path

    def handle_output(self, context, obj):
        if obj is not None:  # if this is a dbt output, then the value will be None
            if not isinstance(obj, pd.DataFrame):
                check.failed(f"Outputs of type {type(obj)} not supported.")

            con = self._connect_duckdb(context).cursor()
            filepath = self._get_path(context)
            # write df to csv file
            obj.to_csv(filepath)

            # create view over that file
            con.execute(f"create schema if not exists {self._schema(context)};")
            con.execute(
                f"create or replace view {self._table_path(context)} as "
                f"select * from '{filepath}';"
            )
            con.close()

    def load_input(self, context):
        check.invariant(not context.has_asset_partitions, "Can't load partitioned inputs")

        if context.dagster_type.typing_type == pd.DataFrame:
            con = self._connect_duckdb(context).cursor()
            ret = con.execute(f"SELECT * FROM {self._table_path(context)}").fetchdf()
            con.close()
            return ret

        check.failed(
            f"Inputs of type {context.dagster_type} not supported. Please specify a valid type "
            "for this input either on the argument of the @asset-decorated function."
        )

    def _get_path(self, context):
        return f"{self._base_path}/{'_'.join(context.asset_key.path)}.csv"

    def _schema(self, context):
        # assume that the schema is the second to last component of the asset key, e.g.
        # AssetKey([database, schema, tablename])
        return context.asset_key.path[-2]

    def _table(self, context):
        # same as above, but for table
        return context.asset_key.path[-1]

    def _table_path(self, context):
        return f"{self._schema(context)}.{self._table(context)}"

    def _connect_duckdb(self, context):
        return duckdb.connect(database=context.resource_config["duckdb_path"], read_only=False)


@io_manager(config_schema={"base_path": Field(str, is_required=False), "duckdb_path": str})
def duckdb_io_manager(init_context):
    return DuckDBCSVIOManager(
        base_path=init_context.resource_config.get("base_path", get_system_temp_directory())
    )