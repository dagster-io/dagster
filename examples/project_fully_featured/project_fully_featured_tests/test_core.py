import tempfile

from dagster_pyspark.resources import PySparkResource
from project_fully_featured.assets import core
from project_fully_featured.resources.hn_resource import HNSnapshotClient
from project_fully_featured.resources.parquet_io_manager import PartitionedParquetIOManager

from dagster import (
    ResourceDefinition,
    fs_io_manager,
    load_assets_from_package_module,
    materialize,
    mem_io_manager,
)


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        pyspark_resource = PySparkResource(spark_conf={})
        result = materialize(
            load_assets_from_package_module(core),
            resources={
                "io_manager": fs_io_manager.configured({"base_dir": temp_dir}),
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": PartitionedParquetIOManager(
                    base_path=temp_dir, pyspark_resource=pyspark_resource
                ),
                "warehouse_io_manager": mem_io_manager,
                "pyspark": pyspark_resource,
                "hn_client": HNSnapshotClient(),
                "dbt": ResourceDefinition.none_resource(),
            },
            partition_key="2020-12-30-00:00",
        )

        assert result.success
