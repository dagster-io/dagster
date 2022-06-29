import numpy as np
import pandas as pd

from dagster import IOManager
from dagster import _check as check
from dagster import io_manager


class PandasIOManager(IOManager):
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
            raise check.CheckError(f"Unsupported object type {type(obj)} for PandasIOManager.")

    def load_input(self, context) -> pd.DataFrame:
        """Load the contents of a table as a pandas DataFrame."""
        model_name = context.upstream_output.asset_key.path[-1]
        return pd.read_sql(f"SELECT * FROM {model_name}", con=self._con)


@io_manager(config_schema={"con_string": str})
def pandas_io_manager(context):
    return PandasIOManager(context.resource_config["con_string"])


# we use the NumpyIOManager as an input manager for an asset to load it as a numpy array rather
# than a Pandas DataFrame (the default loading behavior for assets)
# This is a toy to showcase swapping out input managers
class NumpyIOManager(PandasIOManager):
    def load_input(self, context) -> np.ndarray:
        model_name = context.upstream_output.asset_key.path[-1]
        pd_df = pd.read_sql(f"SELECT * FROM {model_name}", con=self._con)
        return pd_df.to_numpy()


@io_manager(config_schema={"con_string": str})
def numpy_io_manager(context):
    return NumpyIOManager(context.resource_config["con_string"])
