from pathlib import Path

from dagster.components import definitions, load_project_defs


@definitions
def defs():
    return load_project_defs(project_root=Path(__file__).parent.parent)
