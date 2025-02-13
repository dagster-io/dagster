from pathlib import Path

import dagster_components as dg_components

defs = dg_components.build_component_defs(Path(__file__).parent / "components")
