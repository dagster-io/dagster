import os
import textwrap

import pandas as pd
from dagster import AssetKey, EventMetadataEntry, MemoizableIOManager, io_manager


class LocalCsvIOManager(MemoizableIOManager):
    """Translates between Pandas DataFrames and CSVs on the local filesystem."""

    def __init__(self, base_dir):
        self._base_dir = base_dir

    def _get_fs_path(self, asset_key: AssetKey) -> str:
        rpath = os.path.join(self._base_dir, *asset_key.path) + ".csv"
        return os.path.abspath(rpath)

    def handle_output(self, context, obj: pd.DataFrame):
        """This saves the dataframe as a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        obj.to_csv(fpath)
        with open(fpath + ".version", "w") as f:
            f.write(context.version if context.version else "None")

        yield EventMetadataEntry.int(obj.shape[0], "Rows")
        yield EventMetadataEntry.path(fpath, "Path")
        yield EventMetadataEntry.md(obj.head(5).to_markdown(), "Sample")
        yield EventMetadataEntry.text(context.version, "Resolved version")
        yield EventMetadataEntry.table_schema(
            context.dagster_type.metadata["schema"].schema,
            "Schema",
        )


    def load_input(self, context):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        date_col_names = [
            table_col.name
            for table_col in context.upstream_output.dagster_type.metadata["schema"].schema.columns
            if table_col.type == "datetime64[ns]"
        ]
        return pd.read_csv(fpath, parse_dates=date_col_names)

    def has_output(self, context) -> bool:
        fpath = self._get_fs_path(context.asset_key)
        version_fpath = fpath + ".version"
        if not os.path.exists(version_fpath):
            return False
        with open(version_fpath, "r") as f:
            version = f.read()

        return version == context.version


@io_manager
def local_csv_io_manager(context):
    return LocalCsvIOManager(context.instance.storage_directory())


def pandas_columns_to_markdown(dataframe: pd.DataFrame) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Type |
        | ---- | ---- |
    """
        )
        + "\n".join([f"| {name} | {dtype} |" for name, dtype in dataframe.dtypes.iteritems()])
    )
