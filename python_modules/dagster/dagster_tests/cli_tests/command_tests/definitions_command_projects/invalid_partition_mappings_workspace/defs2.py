import dagster as dg

utc = dg.DailyPartitionsDefinition(start_date="2020-01-01")


@dg.asset(deps=[dg.AssetSpec(key="upstream_asset")], partitions_def=utc)
def downstream_asset():
    pass
