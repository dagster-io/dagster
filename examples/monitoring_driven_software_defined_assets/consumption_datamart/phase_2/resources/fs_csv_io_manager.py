from pathlib import Path

import pandas

from dagster import Field, IOManager
from dagster import io_manager


class LocalFileCSVIOManager(IOManager):
    """Translates between Pandas DataFrames and CSVs on the local filesystem."""

    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)

    def handle_output(self, context, obj):
        pass

    def load_input(self, context):
        """This reads a dataframe from a CSV."""

        return pandas.read_csv(str((self.data_folder / Path(*context.asset_key.path[:-1]) /
                                    f"{context.asset_key.path[-1]}.csv").resolve()))


@io_manager(
    {
        "data_folder": Field(str, is_required=True, description="Path to folder containing asset CSVs"),
    }
)
def fs_csv_io_manager(init_context):
    return LocalFileCSVIOManager(data_folder=init_context.resource_config["data_folder"])
