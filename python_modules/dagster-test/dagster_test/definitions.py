from pathlib import Path

from dagster.components import definitions, load_from_defs_folder


@definitions
def defs():
    return load_from_defs_folder(project_root=Path(__file__).parent.parent)
