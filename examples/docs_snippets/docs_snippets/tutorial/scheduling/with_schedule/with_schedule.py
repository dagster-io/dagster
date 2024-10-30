from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    load_assets_from_modules,
)

from . import assets

all_assets = load_assets_from_modules([assets])

# Addition: a ScheduleDefinition targeting all assets and a cron schedule of how frequently to run it
hackernews_schedule = ScheduleDefinition(
    name="hackernews_schedule",
    target=AssetSelection.all(),
    cron_schedule="0 * * * *",  # every hour
)

defs = Definitions(
    assets=all_assets,
    schedules=[hackernews_schedule],
)
