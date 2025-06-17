from pathlib import Path

from my_existing_project.assets import my_asset

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(assets=[my_asset]),
    dg.load_project_defs(project_root=Path(__file__).parent.parent),
)
