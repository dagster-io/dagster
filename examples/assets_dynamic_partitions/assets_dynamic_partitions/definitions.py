from dagster import Definitions, load_assets_from_modules
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler

from . import assets
from .release_sensor import release_sensor

duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])

defs = Definitions(
    assets=load_assets_from_modules([assets]),
    sensors=[release_sensor],
    resources={"warehouse": duckdb_io_manager.configured({"database": "releases.duckdb"})},
)
