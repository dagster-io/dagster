from pathlib import Path

import dagster as dg


@dg.definitions
def defs():
    defs_from_folder = dg.load_from_defs_folder(project_root=Path(__file__).parent.parent)

    return dg.Definitions(
        assets=defs_from_folder.assets,
        jobs=defs_from_folder.jobs,
        schedules=defs_from_folder.schedules,
        sensors=defs_from_folder.sensors,
        asset_checks=defs_from_folder.asset_checks,
        # Add shared I/O manager for cross-repository access
        resources={
            **defs_from_folder.resources,
            "io_manager": dg.FilesystemIOManager(base_dir="~/Documents/dagster_shared_assets"),
        },
    )
