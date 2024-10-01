import wandb
from dagster import (
    AssetExecutionContext,
    AssetIn,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)

partitions_def = MultiPartitionsDefinition(
    {
        "date": DailyPartitionsDefinition(start_date="2023-01-01", end_date="2023-01-05"),
        "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
    }
)


@asset(
    group_name="partitions",
    partitions_def=partitions_def,
    name="my_multi_partitioned_asset",
    compute_kind="wandb",
    metadata={
        "wandb_artifact_configuration": {
            "type": "dataset",
        }
    },
)
def create_my_multi_partitioned_asset(context: AssetExecutionContext):
    """Example writing an Artifact with mutli partitions and custom metadata."""
    partition_key = context.partition_key
    context.log.info(f"Creating partitioned asset for {partition_key}")
    if partition_key == "red|2023-01-02":
        artifact = wandb.Artifact("my_multi_partitioned_asset", "dataset")
        table = wandb.Table(columns=["color"], data=[[partition_key]])
        return artifact.add(table, "default_table_name")
    return partition_key  # e.g. "blue|2023-01-04"


@asset(
    group_name="partitions",
    compute_kind="wandb",
    ins={
        "my_multi_partitioned_asset": AssetIn(
            metadata={
                "wandb_artifact_configuration": {
                    "partitions": {
                        "red|2023-01-02": {
                            "get": "custom_table_name",
                        },
                    },
                },
            },
        )
    },
    output_required=False,
)
def read_all_multi_partitions(context, my_multi_partitioned_asset):
    """Example reading all Artifact partitions from the previous asset."""
    for partition, content in my_multi_partitioned_asset.items():
        context.log.info(f"partition={partition}, content={content}")
