import tempfile

from dagster import (
    FilesystemIOManager,
    ResourceDefinition,
    load_assets_from_package_module,
    materialize,
    mem_io_manager,
)
from dagster_pyspark import pyspark_resource

from project_fully_featured.assets import core
from project_fully_featured.resources.hn_resource import HNSnapshotClient
from project_fully_featured.resources.parquet_io_manager import (
    LocalPartitionedParquetIOManager,
)


def test_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = materialize(
            load_assets_from_package_module(core),
            resources={
                "io_manager": FilesystemIOManager(base_dir=temp_dir),
                "partition_start": ResourceDefinition.string_resource(),
                "partition_end": ResourceDefinition.string_resource(),
                "parquet_io_manager": LocalPartitionedParquetIOManager(
                    base_path=temp_dir, pyspark=pyspark_resource
                ),
                "warehouse_io_manager": mem_io_manager,
                "hn_client": HNSnapshotClient(),
                "dbt": ResourceDefinition.none_resource(),
            },
            partition_key="2020-12-30-00:00",
        )

        assert result.success
