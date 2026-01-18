from pathlib import Path

from dagster import load_from_defs_folder

defs_obj = load_from_defs_folder(project_root=Path(__file__).parent.parent)
