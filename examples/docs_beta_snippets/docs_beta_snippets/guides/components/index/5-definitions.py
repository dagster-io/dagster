from pathlib import Path

import jaffle_platform.defs
from dagster_components import build_defs

defs = build_defs(components_root=jaffle_platform.defs)
