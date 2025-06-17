from pathlib import Path

from dagster import load_defs_folder

defs = load_defs_folder(defs_folder_path=Path(__file__).parent / "defs")
