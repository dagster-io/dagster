from dagster import Definitions, load_assets_from_modules

from project_atproto_dashboard import assets

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)
