from pathlib import Path

import jaffle_platform.defs
from dagster_components import load_defs

defs = load_defs(defs_root=jaffle_platform.defs)
