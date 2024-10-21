from dagster import StaticPartitionsDefinition, asset
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition


@asset
def asset1() -> None: ...


@asset(key_prefix=["some", "key", "prefix"])
def asset_with_prefix() -> None: ...


@asset(deps=[asset1])
def downstream_asset() -> None: ...


@asset(partitions_def=StaticPartitionsDefinition(["one", "two", "three"]))
def partitioned_asset() -> None: ...


@asset(partitions_def=StaticPartitionsDefinition(["apple", "banana", "pear"]))
def differently_partitioned_asset() -> None: ...


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
)
def single_run_partitioned_asset() -> None: ...


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.multi_run(),
)
def multi_run_partitioned_asset() -> None: ...


@asset
def fail_asset() -> None:
    raise Exception("failure")
