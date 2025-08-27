from pathlib import Path

from dagster import load_from_defs_folder

defs = load_from_defs_folder(project_root=Path(__file__).parent.parent)
