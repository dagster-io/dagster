from dagster import Definitions, load_assets_from_modules

from . import mlflow_assets

all_assets = load_assets_from_modules([mlflow_assets])

defs = Definitions(
    assets=all_assets,
)
