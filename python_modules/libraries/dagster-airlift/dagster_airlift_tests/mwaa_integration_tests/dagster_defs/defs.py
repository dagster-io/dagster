from pathlib import Path

from dagster import load_defs_folder

defs_obj = load_defs_folder(Path(__file__).parent / "inner")
