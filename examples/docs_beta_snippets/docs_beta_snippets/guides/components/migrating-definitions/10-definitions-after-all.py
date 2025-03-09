from pathlib import Path

import dagster_components as dg_components
import my_existing_project.defs

defs = dg_components.build_defs(my_existing_project.defs)
