import dagster as dg
from my_existing_project.assets import my_asset

defs = dg.Definitions(
    assets=[my_asset],
)
