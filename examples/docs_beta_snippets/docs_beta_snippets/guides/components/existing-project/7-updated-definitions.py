from pathlib import Path
import dagster as dg
import dagster_components as dg_components
from my_existing_project import assets

all_assets = dg.load_assets_from_modules([assets])

defs = dg.Definitions.merge(
    dg.Definitions(assets=all_assets),
    dg_components.build_component_defs(Path(__file__).parent / "components"),
)
