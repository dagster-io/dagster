from pathlib import Path

from dagster import load_project_defs

defs = load_project_defs(project_root=Path(__file__).parent.parent)
