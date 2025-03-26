# isort: skip_file
from my_existing_project import assets

import dagster as dg

all_assets = dg.load_assets_from_modules([assets])

defs = dg.Definitions(
    assets=all_assets,
)
