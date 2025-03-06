from pathlib import Path

import jaffle_platform.defs
from dagster_components import build_component_defs

defs = build_component_defs(components_root=jaffle_platform.defs)
