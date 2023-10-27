from dagster import AutoMaterializePolicy, DailyPartitionsDefinition, asset, repository

### Non partitioned ##


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_upstream():
    return 3


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_0_point_5(eager_upstream):
    return eager_upstream + 1


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), deps=[eager_upstream])
def eager_downstream_1(eager_downstream_0_point_5):
    return eager_downstream_0_point_5 + 1


### Partitioned ##

daily_partitions_def = DailyPartitionsDefinition(start_date="2023-02-01")


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), partitions_def=daily_partitions_def)
def eager_upstream_partitioned():
    return 3


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), partitions_def=daily_partitions_def)
def eager_downstream_0_point_5_partitioned(eager_upstream_partitioned):
    return eager_upstream_partitioned + 1


@asset(
    auto_materialize_policy=AutoMaterializePolicy.eager(),
    partitions_def=daily_partitions_def,
    deps=[eager_downstream_0_point_5_partitioned],
)
def eager_downstream_1_partitioned(eager_upstream_partitioned):
    return eager_upstream_partitioned + 1


@repository
def auto_materialize_repo_1():
    return [
        eager_upstream,
        eager_downstream_0_point_5,
        eager_downstream_1,
        eager_upstream_partitioned,
        eager_downstream_1_partitioned,
        eager_downstream_0_point_5_partitioned,
    ]
