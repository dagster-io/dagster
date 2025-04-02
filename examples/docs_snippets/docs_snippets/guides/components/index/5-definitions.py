from pathlib import Path

import jaffle_platform.defs

from dagster.components import load_defs

defs = load_defs(defs_root=jaffle_platform.defs)
