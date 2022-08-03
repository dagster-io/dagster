import pandas as pd

from dagster import IOManager, io_manager


class DbIOManager(IOManager):
    """Sample IOManager to handle loading the contents of tables as pandas DataFrames.

    Does not handle cases where data is written to different schemas for different outputs, and
    uses the name of the asset key as the table name.
    """

    def __init__(self, con_string: str):
        self._con = con_string

    def handle_output(self, context, obj):
        if isinstance(obj, pd.DataFrame):
            # write df to table
            obj.to_sql(name=context.asset_key.path[-1], con=self._con, if_exists="replace")
        elif obj is None:
            # dbt has already written the data to this table
            pass
        else:
            raise ValueError(f"Unsupported object type {type(obj)} for DbIOManager.")

    def load_input(self, context) -> pd.DataFrame:
        """Load the contents of a table as a pandas DataFrame."""
        model_name = context.upstream_output.asset_key.path[-1]
        return pd.read_sql(f"SELECT * FROM {model_name}", con=self._con)


@io_manager(config_schema={"con_string": str})
def db_io_manager(context):
    return DbIOManager(context.resource_config["con_string"])
