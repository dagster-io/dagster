from pathlib import Path

from my_existing_project.assets import my_asset

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(assets=[my_asset]),
    dg.load_defs_folder(Path(__file__).parent / "defs"),
)
