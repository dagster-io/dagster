from pathlib import Path

import dagster_components as dg_components

import dagster as dg
from my_existing_project.analytics import definitions as analytics_definitions
from my_existing_project.elt import definitions as elt_definitions

defs = dg.Definitions.merge(
    dg.load_definitions_from_module(elt_definitions),
    dg.load_definitions_from_module(analytics_definitions),
    dg_components.build_component_defs(Path(__file__).parent / "components"),
)
