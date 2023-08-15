# ruff: isort: skip_file
all_assets = None

# start_imports_and_definitions
from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
    FilesystemIOManager,  # Update the imports at the top of the file to also include this
)

hackernews_job = define_asset_job("hackernews_job", selection=AssetSelection.all())

hackernews_schedule = ScheduleDefinition(
    job=hackernews_job, cron_schedule="0 * * * *"  # every hour
)

io_manager = FilesystemIOManager(
    base_dir="data",  # Path is built relative to where `dagster dev` is run
)
# end_imports_and_definitions

# start_update_defs
defs = Definitions(
    assets=all_assets,
    schedules=[hackernews_schedule],
    resources={
        "io_manager": io_manager,
    },
)
# end_update_defs
