from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component_defs_builder import build_component_defs

defs = build_component_defs(Path(__file__).parent / "components")

if __name__ == "__main__":
    Definitions.validate_loadable(defs)
