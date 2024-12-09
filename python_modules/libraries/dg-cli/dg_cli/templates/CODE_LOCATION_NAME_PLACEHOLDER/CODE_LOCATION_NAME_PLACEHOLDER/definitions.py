from pathlib import Path

from dagster_components.core.component_defs_builder import (
    build_defs_from_toplevel_components_folder,
)

defs = build_defs_from_toplevel_components_folder(
    path=Path(__file__).parent,
)
