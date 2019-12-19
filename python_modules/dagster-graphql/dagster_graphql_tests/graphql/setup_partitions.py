from dagster import Partition, PartitionSetDefinition, repository_partitions

integer_set = PartitionSetDefinition(
    name="integer_partition",
    pipeline_name="no_config_pipeline",
    solid_subset=['return_hello'],
    mode="default",
    partition_fn=lambda: [Partition(i) for i in range(10)],
    environment_dict_fn_for_partition=lambda _: {"storage": {"filesystem": {}}},
)


enum_set = PartitionSetDefinition(
    name="enum_partition",
    pipeline_name="noop_pipeline",
    partition_fn=lambda: ["one", "two", "three"],
    environment_dict_fn_for_partition=lambda _: {"storage": {"filesystem": {}}},
)


@repository_partitions
def define_partitions():
    return [integer_set, enum_set]
