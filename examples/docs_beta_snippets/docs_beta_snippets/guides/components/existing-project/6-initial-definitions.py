import dagster as dg
from my_existing_project import assets

all_assets = dg.load_assets_from_modules([assets])

defs = dg.Definitions(
    assets=all_assets,
)
