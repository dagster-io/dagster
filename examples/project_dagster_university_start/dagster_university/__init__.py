from dagster import Definitions, load_assets_from_modules

from .assets import trips, metrics

trip_assets = load_assets_from_modules([trips])
metric_assets = load_assets_from_modules([metrics])

defs = Definitions(
    assets=trip_assets + metric_assets,
)
