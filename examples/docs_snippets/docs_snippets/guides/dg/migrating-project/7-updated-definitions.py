import my_existing_project.defs
from my_existing_project.assets import my_asset

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(assets=[my_asset]),
    dg.components.load_defs(my_existing_project.defs),
)
