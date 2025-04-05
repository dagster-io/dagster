from pathlib import Path

import stocks_dsl_component_yaml.defs
from dagster_components import load_defs

defs = load_defs(defs_root=stocks_dsl_component_yaml.defs)
