from pathlib import Path
import dagster as dg

defs = dg.load_project_defs(Path(__file__).parent.parent)
