from dagster import Definitions, load_assets_from_modules

from .assets import trips

trip_assets = load_assets_from_modules([trips])

defs = Definitions(
    assets=trip_assets
)
