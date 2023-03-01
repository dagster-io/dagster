from dagster import DagsterInstance, load_assets_from_modules, materialize_to_memory
from dagster_test.toys import dynamic_asset_partitions
from dagster_test.toys.dynamic_asset_partitions import (
    customers_partitions_def,
    defs,
)


def test_assets():
    assets = load_assets_from_modules([dynamic_asset_partitions])

    with DagsterInstance.ephemeral() as instance:
        customers_partitions_def.add_partitions(["pepsi", "coca_cola"], instance=instance)
        assert materialize_to_memory(assets, partition_key="pepsi", instance=instance).success


def test_job():
    with DagsterInstance.ephemeral() as instance:
        customers_partitions_def.add_partitions(["pepsi", "coca_cola"], instance=instance)
        assert (
            defs.get_job_def("dynamic_partitions_job")
            .execute_in_process(partition_key="pepsi", instance=instance)
            .success
        )
