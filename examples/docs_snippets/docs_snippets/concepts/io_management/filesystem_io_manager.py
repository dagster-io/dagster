# start_marker
import pandas as pd
from upath import UPath

from dagster import InputContext, OutputContext, UPathIOManager


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
from typing import Optional

from dagster import ConfigurableIOManagerFactory, EnvVar


class LocalPandasParquetIOManager(ConfigurableIOManagerFactory):
    base_path: Optional[str] = None

    def create_io_manager(self, context) -> PandasParquetIOManager:
        base_path = UPath(self.base_path or context.instance.storage_directory())
        return PandasParquetIOManager(base_path=base_path)


class S3ParquetIOManager(ConfigurableIOManagerFactory):
    base_path: str

    aws_access_key: str = EnvVar("AWS_ACCESS_KEY_ID")
    aws_secret_key: str = EnvVar("AWS_SECRET_ACCESS_KEY")

    def create_io_manager(self, context) -> PandasParquetIOManager:
        base_path = UPath(self.base_path)
        assert str(base_path).startswith("s3://"), base_path
        return PandasParquetIOManager(base_path=base_path)


# end_marker
