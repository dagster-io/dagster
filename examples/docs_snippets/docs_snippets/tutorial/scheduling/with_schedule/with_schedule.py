import dagster as dg

from . import assets

all_assets = dg.load_assets_from_modules([assets])

# Addition: a dg.ScheduleDefinition targeting all assets and a cron schedule of how frequently to run it
hackernews_schedule = dg.ScheduleDefinition(
    name="hackernews_schedule",
    target=dg.AssetSelection.all(),
    cron_schedule="0 * * * *",  # every hour
)

defs = dg.Definitions(
    assets=all_assets,
    schedules=[hackernews_schedule],
)
