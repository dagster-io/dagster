from pathlib import Path

from dagster_components import build_component_defs

defs = build_component_defs(code_location_root=Path(__file__).parent.parent)
