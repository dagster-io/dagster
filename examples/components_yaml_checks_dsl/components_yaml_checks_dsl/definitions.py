from pathlib import Path

from dagster import definitions, load_defs_folder


@definitions
def defs():
    return load_defs_folder(defs_root=Path(__file__).parent / "defs")
