import wandb
from dagster import AssetIn, StaticPartitionsDefinition, asset

partitions_def = StaticPartitionsDefinition(["red", "orange", "yellow", "blue", "green"])

ARTIFACT_NAME = "my_advanced_configuration_partitioned_asset"


@asset(
    group_name="partitions",
    partitions_def=partitions_def,
    name=ARTIFACT_NAME,
    compute_kind="wandb",
    metadata={
        "wandb_artifact_configuration": {
            "aliases": ["special_alias"],
        }
    },
)
def write_advanced_artifact(context):
    """Example writing an Artifact with partitions and custom metadata."""
    artifact = wandb.Artifact(ARTIFACT_NAME, "dataset")
    partition_key = context.asset_partition_key_for_output()

    if partition_key == "red":
        return "red"
    elif partition_key == "orange":
        return wandb.Table(columns=["color"], data=[["orange"]])
    elif partition_key == "yellow":
        table = wandb.Table(columns=["color"], data=[["yellow"]])
        artifact.add(table, "custom_table_name")
    else:
        table = wandb.Table(columns=["color", "value"], data=[[partition_key, 1]])
        artifact.add(table, "default_table_name")
    return artifact


@asset(
    group_name="partitions",
    compute_kind="wandb",
    ins={
        "partitions": AssetIn(
            key=ARTIFACT_NAME,
            metadata={
                "wandb_artifact_configuration": {
                    "partitions": {
                        # The wildcard "*" means "all non-configured partitions"
                        "*": {
                            "get": "default_table_name",
                        },
                        # You can override the wildcard for specific partition using their key
                        "yellow": {
                            "get": "custom_table_name",
                        },
                        # You can collect a specific Artifact version
                        "orange": {
                            "version": "v0",
                        },
                        # You can collect a specific alias, note you must specify the 'get' value.
                        # This is because the wildcard is only applied to partitions that haven't
                        # been configured.
                        "blue": {
                            "alias": "special_alias",
                            "get": "default_table_name",
                        },
                    },
                },
            },
        )
    },
    output_required=False,
)
def read_objects_directly(context, partitions):
    """Example reading all Artifact partitions from the previous asset."""
    for partition, content in partitions.items():
        context.log.info(f"partition={partition}, type={type(content)}")
        if partition == "red":
            context.log.info(content)
        elif partition == "orange":
            # The orange partition was a raw W&B Table, the IO Manager wrapped that Table in an
            # Artifact. The default name for the table is 'Table'. We could have also set
            # the partition 'get' config to receive the table directly instead of the Artifact.
            context.log.info(content.get("Table").get_column("color"))
        else:
            context.log.info(content.get_column("color"))
