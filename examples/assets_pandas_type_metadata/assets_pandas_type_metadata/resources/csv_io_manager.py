import os
import textwrap

import pandas as pd
from dagster import (
    AssetKey,
    MemoizableIOManager,
    MetadataEntry,
    TableSchemaMetadataValue,
    io_manager,
)
from dagster._core.definitions.metadata import MetadataValue


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
        with open(fpath + ".version", "w", encoding="utf8") as f:
            f.write(context.version if context.version else "None")

        yield MetadataEntry("Rows", value=MetadataValue.int(obj.shape[0]))
        yield MetadataEntry("Path", value=MetadataValue.path(fpath))
        yield MetadataEntry("Sample", value=MetadataValue.md(obj.head(5).to_markdown()))
        yield MetadataEntry("Resolved version", value=MetadataValue.text(context.version))  # type: ignore
        yield MetadataEntry(
            "Schema",
            value=MetadataValue.table_schema(self.get_schema(context.dagster_type)),
        )

    def get_schema(self, dagster_type):
        schema_entry = next(
            (
                x
                for x in dagster_type.metadata_entries
                if isinstance(x.value, TableSchemaMetadataValue)
            ),
            None,
        )
        assert schema_entry
        return schema_entry.value.schema

    def load_input(self, context):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(context.asset_key)
        date_col_names = [
            table_col.name
            for table_col in self.get_schema(context.upstream_output.dagster_type).columns
            if table_col.type == "datetime64[ns]"
        ]
        return pd.read_csv(fpath, parse_dates=date_col_names)

    def has_output(self, context) -> bool:
        fpath = self._get_fs_path(context.asset_key)
        version_fpath = fpath + ".version"
        if not os.path.exists(version_fpath):
            return False
        with open(version_fpath, "r", encoding="utf8") as f:
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
