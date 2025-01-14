from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component_defs_builder import build_component_defs

defs = build_component_defs(code_location_root=Path(__file__).parent.parent)

if __name__ == "__main__":
    Definitions.validate_loadable(defs)
