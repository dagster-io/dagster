from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

from .resources import DataGeneratorResource


@asset
def foo_asset():
    return 1


all_assets = [foo_asset]
job = define_asset_job(
    name="hackernews_top_stories_job",
    selection=AssetSelection.all(),
)
hackernews_schedule = ScheduleDefinition(
    name="hackernews_top_stories_schedule",
    cron_schedule="1 1 1 * *",
    job=job,
)

# start_add_resource
from .resources import DataGeneratorResource

# ...

datagen = DataGeneratorResource()  # Make the resource

defs = Definitions(
    assets=all_assets,
    schedules=[hackernews_schedule],
    resources={
        "hackernews_api": datagen,  # Add the newly-made resource here
    },
)
# end_add_resource
