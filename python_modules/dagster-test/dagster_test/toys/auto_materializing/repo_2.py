from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    DailyPartitionsDefinition,
    SourceAsset,
    asset,
    repository,
)

eager_downstream_1_source = SourceAsset(AssetKey(["eager_downstream_1"]))

### Non partitioned ###


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_2(eager_downstream_1):
    return eager_downstream_1 + 2


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_3(eager_downstream_1):
    return eager_downstream_1 + 3


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_4(eager_downstream_2, eager_downstream_3):
    return eager_downstream_2 + eager_downstream_3


### Partitioned ###

daily_partitions_def = DailyPartitionsDefinition(start_date="2023-02-01")

eager_downstream_1_source_partitioned = SourceAsset(
    AssetKey(["eager_downstream_1_partitioned"]), partitions_def=daily_partitions_def
)


@asset(partitions_def=daily_partitions_def, auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_2_partitioned(eager_downstream_1_partitioned):
    return eager_downstream_1_partitioned + 2


@asset(partitions_def=daily_partitions_def, auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_3_partitioned(eager_downstream_1_partitioned):
    return eager_downstream_1_partitioned + 3


@asset(partitions_def=daily_partitions_def, auto_materialize_policy=AutoMaterializePolicy.eager())
def eager_downstream_4_partitioned(eager_downstream_2_partitioned, eager_downstream_3_partitioned):
    return eager_downstream_2_partitioned + eager_downstream_3_partitioned


@repository
def auto_materialize_repo_2():
    return [
        eager_downstream_2,
        eager_downstream_3,
        eager_downstream_1_source,
        eager_downstream_4,
        eager_downstream_2_partitioned,
        eager_downstream_3_partitioned,
        eager_downstream_1_source_partitioned,
        eager_downstream_4_partitioned,
    ]
