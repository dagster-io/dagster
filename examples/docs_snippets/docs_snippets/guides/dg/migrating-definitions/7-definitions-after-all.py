from pathlib import Path
import dagster as dg

defs = dg.load_defs_folder(Path(__file__).parent / "defs")
