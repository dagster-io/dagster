from pathlib import Path

from dagster._nope.project import NopeProject

defs = NopeProject.make_definitions(
    defs_path=Path(__file__).resolve().parent / Path("by_file_defs")
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
