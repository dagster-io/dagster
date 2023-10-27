from dagster import AutoMaterializePolicy, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-10-10"),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def asset1():
    ...


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-10-10"),
    auto_materialize_policy=AutoMaterializePolicy.eager(),
    deps=[asset1],
)
def asset2():
    ...
