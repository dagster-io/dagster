from pathlib import Path

from dagster.components import definitions, load_defs_folder


@definitions
def defs():
    defs_path = Path(__file__).parent / "defs"
    return load_defs_folder(defs_path)
