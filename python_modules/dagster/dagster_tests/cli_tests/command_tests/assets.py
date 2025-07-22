import dagster as dg
from dagster import AssetExecutionContext
from dagster._core.definitions.backfill_policy import BackfillPolicy


@dg.asset
def asset1() -> None: ...


@dg.asset(key_prefix=["some", "key", "prefix"])
def asset_with_prefix() -> None: ...


@dg.asset(deps=[asset1])
def downstream_asset() -> None: ...


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["one", "two", "three"]))
def partitioned_asset() -> None: ...


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["apple", "banana", "pear"]))
def differently_partitioned_asset() -> None: ...


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.single_run(),
)
def single_run_partitioned_asset() -> None: ...


@dg.asset(
    partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01"),
    backfill_policy=BackfillPolicy.multi_run(),
)
def multi_run_partitioned_asset() -> None: ...


class MyConfig(dg.Config):
    some_prop: str


@dg.asset
def asset_with_config(context: AssetExecutionContext, config: MyConfig):
    context.log.info(f"some_prop:{config.some_prop}")


@dg.asset
def asset_assert_with_config(context: AssetExecutionContext, config: MyConfig):
    assert config.some_prop == "foo"
    context.log.info(f"some_prop:{config.some_prop}")


@dg.asset
def fail_asset() -> None:
    raise Exception("failure")
