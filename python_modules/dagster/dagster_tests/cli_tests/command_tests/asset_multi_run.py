from dagster import asset
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.multi_run(),
)
def multi_run_partitioned_asset() -> None: ...
