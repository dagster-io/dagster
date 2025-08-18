import dagster as dg

hourly_partitions_def = dg.HourlyPartitionsDefinition("2023-10-01-00:00")
daily_partitions_def = dg.DailyPartitionsDefinition("2023-10-01")


class ConfigA(dg.Config):
    a: int


class ConfigB(dg.Config):
    b: str


class ConfigCrazy(dg.Config):
    c: ConfigA
    d: ConfigB
    e: float


@dg.asset(partitions_def=hourly_partitions_def)
def hourly(config: ConfigA):
    pass


@dg.asset(partitions_def=daily_partitions_def, deps=[hourly])
def daily(config: ConfigB):
    pass


@dg.asset(partitions_def=daily_partitions_def, deps=[daily])
def other_daily(config: ConfigB):
    pass


@dg.asset(partitions_def=daily_partitions_def, deps=[hourly])
def unrelated(config: ConfigCrazy):
    pass


@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2023-10-02"), deps=["C"])
def middle(): ...


@dg.multi_asset(
    specs=[
        dg.AssetSpec("C", partitions_def=daily_partitions_def),
        dg.AssetSpec("D", partitions_def=daily_partitions_def, deps=[middle]),
    ],
    can_subset=True,
)
def c_and_d_asset(context: dg.AssetExecutionContext, config: ConfigA):
    for asset_key in context.selected_asset_keys:
        yield dg.MaterializeResult(asset_key=asset_key)


defs = dg.Definitions(
    assets=[hourly, daily, other_daily, unrelated, c_and_d_asset, middle],
    jobs=[dg.define_asset_job("daily_job", selection=[daily, other_daily])],
)
