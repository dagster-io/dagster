import os
import textwrap
from typing import Optional

import pandas as pd
from dagster import AssetKey, ConfigurableIOManager, MemoizableIOManager, TableSchemaMetadataValue
from dagster._core.definitions.metadata import MetadataValue
from dagster._utils.cached_method import cached_method
from pydantic import Field


class LocalCsvIOManager(ConfigurableIOManager, MemoizableIOManager):
    """Translates between Pandas DataFrames and CSVs on the local filesystem."""

    base_dir: Optional[str] = Field(default=None)

    @property
    @cached_method
    def resolved_base_dir(self) -> str:
        if self.base_dir:
            return self.base_dir
        resource_context = self.get_resource_context()
        if resource_context.instance is not None:
            return resource_context.instance.storage_directory()
        else:
            return os.getenv("DAGSTER_HOME", ".")

    def _get_fs_path(self, asset_key: AssetKey) -> str:
        rpath = os.path.join(self.resolved_base_dir, *asset_key.path) + ".csv"
        return os.path.abspath(rpath)

    def handle_output(self, context, obj: pd.DataFrame):
        """This saves the dataframe as a CSV."""
        fpath = self._get_fs_path(asset_key=context.asset_key)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        obj.to_csv(fpath)
        with open(fpath + ".version", "w", encoding="utf8") as f:
            f.write(context.version if context.version else "None")

        context.add_output_metadata(
            {
                "Rows": MetadataValue.int(obj.shape[0]),
                "Path": MetadataValue.path(fpath),
                "Sample": MetadataValue.md(obj.head(5).to_markdown()),
                "Resolved version": MetadataValue.text(context.version),  # type: ignore
                "Schema": MetadataValue.table_schema(self.get_schema(context.dagster_type)),
            }
        )

    def get_schema(self, dagster_type):
        schema_value = next(
            (x for x in dagster_type.metadata.values() if isinstance(x, TableSchemaMetadataValue)),
            None,
        )
        assert schema_value
        return schema_value.schema

    def load_input(self, context):
        """This reads a dataframe from a CSV."""
        fpath = self._get_fs_path(asset_key=context.asset_key)
        date_col_names = [
            table_col.name
            for table_col in self.get_schema(context.upstream_output.dagster_type).columns
            if table_col.type == "datetime64[ns]"
        ]
        return pd.read_csv(fpath, parse_dates=date_col_names)

    def has_output(self, context) -> bool:
        fpath = self._get_fs_path(asset_key=context.asset_key)
        version_fpath = fpath + ".version"
        if not os.path.exists(version_fpath):
            return False
        with open(version_fpath, "r", encoding="utf8") as f:
            version = f.read()

        return version == context.version


def pandas_columns_to_markdown(dataframe: pd.DataFrame) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Type |
        | ---- | ---- |
    """
        )
        + "\n".join([f"| {name} | {dtype} |" for name, dtype in dataframe.dtypes.items()])
    )
