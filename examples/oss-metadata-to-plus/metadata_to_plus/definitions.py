from dagster import Definitions

from .existing_definitions import (
    asset_2,
    asset_3,
    my_daily_partitioned_asset,
    my_partitioned_schedule,
)
from .migrate_metadata_job import migrate_metadata_asset, migrate_metadata_job

defs = Definitions(
    assets=[my_daily_partitioned_asset, asset_2, asset_3, migrate_metadata_asset],
    schedules=[my_partitioned_schedule],
    jobs=[migrate_metadata_job],
)
