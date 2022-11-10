# start_marker
import json
from typing import Any

import pandas as pd
from upath import UPath

from dagster import InputContext, OutputContext, UPathIOManager


class JSONIOManager(UPathIOManager):
    extension: str = ".json"

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
        with path.open("w") as file:
            json.dump(obj, file)

    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        with path.open("r") as file:
            return json.load(file)


class PandasParquetIOManager(UPathIOManager):
    extension: str = ".parquet"

    def dump_to_path(self, context: OutputContext, obj: pd.DataFrame, path: UPath):
        with path.open("wb") as file:
            obj.to_parquet(file)

    def load_from_path(self, context: InputContext, path: UPath) -> pd.DataFrame:
        with path.open("rb") as file:
            return pd.read_parquet(file)


# end_marker
