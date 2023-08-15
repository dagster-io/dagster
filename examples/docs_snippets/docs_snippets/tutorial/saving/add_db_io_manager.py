# ruff: isort: skip_file
all_assets = None
hackernews_schedule = None

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

# start_imports_and_definitions
from dagster_duckdb_pandas import DuckDBPandasIOManager

# Add the imports to the top
# These imports let you define how Dagster communicates with DuckDB

# Insert this section anywhere above your `defs = Definitions(...)`
database_io_manager = DuckDBPandasIOManager(database="analytics.hackernews")

# Update your Definitions
defs = Definitions(
    assets=all_assets,
    schedules=[hackernews_schedule],
    resources={
        "io_manager": io_manager,
        "database_io_manager": database_io_manager,  # Define the I/O manager here
    },
)
# end_imports_and_definitions
