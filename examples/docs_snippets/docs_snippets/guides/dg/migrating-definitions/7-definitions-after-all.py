from pathlib import Path
import dagster as dg

defs = dg.load_project_defs(project_root=Path(__file__).parent.parent)
