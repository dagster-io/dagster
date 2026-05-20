from dagster import Definitions

from .existing_definitions import my_daily_partitioned_asset, my_partitioned_schedule
from .migrate_metadata_job import migrate_metadata_asset, migrate_metadata_job

defs = Definitions(
    assets=[my_daily_partitioned_asset, migrate_metadata_asset],
    schedules=[my_partitioned_schedule],
    jobs=[migrate_metadata_job],
)
