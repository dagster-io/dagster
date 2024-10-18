from pathlib import Path

from dagster_looker import build_looker_asset_specs

import dagster as dg

looker_specs = build_looker_asset_specs(project_dir=Path("my_looker_project"))
looker_assets = dg.external_assets_from_specs(looker_specs)

defs = dg.Definitions(assets=looker_assets)
