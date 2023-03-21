from dagster import (
    DagsterInstance,
    MultiPartitionKey,
    materialize_to_memory,
)
from dagster_test.toys.partitioned_assets.dynamic_asset_partitions import (
    customers_partitions_def,
    defs,
    dynamic_partitions_asset1,
    dynamic_partitions_asset2,
    multipartitioned_with_dynamic_dimension,
)


def test_assets():
    with DagsterInstance.ephemeral() as instance:
        instance.add_dynamic_partitions(customers_partitions_def.name, ["pepsi", "coca_cola"])

        assert materialize_to_memory(
            [dynamic_partitions_asset1, dynamic_partitions_asset2],
            partition_key="pepsi",
            instance=instance,
        ).success
        assert materialize_to_memory(
            [multipartitioned_with_dynamic_dimension],
            partition_key=MultiPartitionKey({"customers": "pepsi", "daily": "2023-01-01"}),
            instance=instance,
        ).success


def test_job():
    with DagsterInstance.ephemeral() as instance:
        instance.add_dynamic_partitions(customers_partitions_def.name, ["pepsi", "coca_cola"])
        assert (
            defs.get_job_def("dynamic_partitions_job")
            .execute_in_process(partition_key="pepsi", instance=instance)
            .success
        )
