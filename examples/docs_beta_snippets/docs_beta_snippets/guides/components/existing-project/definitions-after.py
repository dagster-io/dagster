from pathlib import Path

import dagster_components as dg_components

import dagster as dg

defs = dg.Definitions.merge(
    dg.Definitions(assets=[]),
    dg_components.build_component_defs(Path(__file__).parent / "components"),
)
