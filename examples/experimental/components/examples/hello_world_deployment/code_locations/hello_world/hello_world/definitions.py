import dagster as dg
from dagster_components import build_component_defs

from . import components

defs = build_component_defs(components)

if __name__ == "__main__":
    dg.Definitions.validate_loadable(defs)
