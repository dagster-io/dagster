import dagster as dg
from dagster_components import load_defs

from . import components

defs = load_defs(components)

if __name__ == "__main__":
    dg.Definitions.validate_loadable(defs)
