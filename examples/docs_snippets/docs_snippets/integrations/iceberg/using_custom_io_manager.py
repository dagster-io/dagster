import pyarrow as pa
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager

from dagster import (
    AssetExecutionContext,
    AssetIn,
    DailyPartitionsDefinition,
    Definitions,
    DimensionPartitionMapping,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    MultiToSingleDimensionPartitionMapping,
    SpecificPartitionsPartitionMapping,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    asset,
)

warehouse_path = "/tmp/warehouse"

# start_defining_the_io_manager

resources = {
    "io_manager": PyArrowIcebergIOManager(
        name="my_catalog",
        config=IcebergCatalogConfig(
            properties={
                "type": "sql",
                "uri": f"sqlite:///{warehouse_path}/pyiceberg_catalog.db",
                "warehouse": f"file://{warehouse_path}",
            }
        ),
        namespace="my_schema",
    )
}

# end_defining_the_io_manager


# start_supported_partition_mapping


@asset(
    key_prefix=["my_schema"],
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    ins={
        "multi_partitioned_asset": AssetIn(
            ["my_schema", "multi_partitioned_asset_1"],
            partition_mapping=MultiToSingleDimensionPartitionMapping(
                partition_dimension_name="date"
            ),
        )
    },
    metadata={
        "partition_expr": "date_column",
    },
)
def single_partitioned_asset_date(multi_partitioned_asset: pa.Table) -> pa.Table: ...


# end_supported_partition_mapping


# start_unsupported_partition_mapping


@asset(
    partitions_def=MultiPartitionsDefinition(
        partitions_defs={
            "date": DailyPartitionsDefinition(
                start_date="2022-01-01",
                end_date="2022-01-10",
            ),
            "letter": StaticPartitionsDefinition(["a", "b", "c"]),
        },
    ),
    key_prefix=["my_schema"],
    metadata={"partition_expr": {"time": "time", "letter": "letter"}},
    ins={
        "multi_partitioned_asset": AssetIn(
            ["my_schema", "multi_partitioned_asset_1"],
            partition_mapping=MultiPartitionMapping(
                {
                    "color": DimensionPartitionMapping(
                        dimension_name="letter",
                        partition_mapping=StaticPartitionMapping(
                            {"blue": "a", "red": "b", "yellow": "c"}
                        ),
                    ),
                    "date": DimensionPartitionMapping(
                        dimension_name="date",
                        partition_mapping=SpecificPartitionsPartitionMapping(
                            ["2022-01-01", "2024-01-01"]
                        ),
                    ),
                }
            ),
        )
    },
)
def mapped_multi_partition(
    context: AssetExecutionContext, multi_partitioned_asset: pa.Table
) -> pa.Table: ...


# end_unsupported_partition_mapping


defs = Definitions(
    assets=[single_partitioned_asset_date, mapped_multi_partition], resources=resources
)
