from pathlib import Path

from dagster._components import build_defs_from_toplevel_components_folder

defs = build_defs_from_toplevel_components_folder(
    path=Path(__file__).parent,
)
