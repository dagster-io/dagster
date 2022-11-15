# start_marker
import pandas as pd
from upath import UPath

from dagster import (
    Field,
    InitResourceContext,
    InputContext,
    OutputContext,
    StringSource,
    UPathIOManager,
    io_manager,
)


class PandasParquetIOManager(UPathIOManager):
    extension: str = ".parquet"

    def dump_to_path(self, context: OutputContext, obj: pd.DataFrame, path: UPath):
        with path.open("wb") as file:
            obj.to_parquet(file)

    def load_from_path(self, context: InputContext, path: UPath) -> pd.DataFrame:
        with path.open("rb") as file:
            return pd.read_parquet(file)


# end_class_marker

# the IO Manager can be used with any filesystem (see https://github.com/fsspec/universal_pathlib)

# start_def_marker
@io_manager(config_schema={"base_path": Field(str, is_required=False)})
def local_pandas_parquet_io_manager(
    init_context: InitResourceContext,
) -> PandasParquetIOManager:
    assert init_context.instance is not None  # to please mypy
    base_path = UPath(
        init_context.resource_config.get(
            "base_path", init_context.instance.storage_directory()
        )
    )
    return PandasParquetIOManager(base_path=base_path)


@io_manager(
    config_schema={
        "base_path": Field(str, is_required=True),
        "AWS_ACCESS_KEY_ID": StringSource,
        "AWS_SECRET_ACCESS_KEY": StringSource,
    }
)
def s3_parquet_io_manager(init_context: InitResourceContext) -> PandasParquetIOManager:
    # `UPath` will read boto env vars.
    # The credentials can also be taken from the config and passed to `UPath` directly.
    base_path = UPath(init_context.resource_config.get("base_path"))
    assert str(base_path).startswith("s3://"), base_path
    return PandasParquetIOManager(base_path=base_path)


# end_marker
