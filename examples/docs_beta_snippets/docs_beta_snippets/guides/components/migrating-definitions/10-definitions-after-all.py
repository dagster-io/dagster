from pathlib import Path

import dagster_components as dg_components
from my_existing_project import defs as component_defs

defs = dg_components.build_component_defs(component_defs)
