from pathlib import Path

import dagster as dg
from dagster_components import build_component_defs

defs = build_component_defs(Path(__file__).parent / "components")

if __name__ == "__main__":
    dg.Definitions.validate_loadable(defs)
