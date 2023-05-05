from typing import List

from dagster import (
    In,
    OpExecutionContext,
    Out,
    job,
    make_values_resource,
    op,
    static_partitioned_config,
)
from dagster_wandb import wandb_artifacts_io_manager, wandb_resource

AWS_REGIONS = [
    "us-west-1",
    "eu-west-1",
    "ap-southeast-2",
]
ARTIFACT_NAME = "my_partitioned_artifact"
ARTIFACT_TYPE = "dataset"


@static_partitioned_config(partition_keys=AWS_REGIONS)
def region(partition_key: str):
    return {
        "ops": {
            "write_partitioned_artifact": {
                "config": {"aws_region": partition_key},
            },
            "read_partitioned_artifact": {
                "config": {"aws_region": partition_key},
            },
        }
    }


@op(
    config_schema={"aws_region": str},
    out=Out(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        }
    ),
)
def write_partitioned_artifact() -> List[int]:
    """Example of a simple op that writes a partitioned Artifact."""
    return [1, 2, 3]


@op(
    config_schema={"aws_region": str},
    ins={
        "content": In(
            metadata={
                "wandb_artifact_configuration": {
                    "name": ARTIFACT_NAME,
                }
            }
        )
    },
)
def read_partitioned_artifact(context: OpExecutionContext, content: List[int]) -> None:
    """Example of a simple op that reads a partitioned Artifact."""
    context.log.info(f"Result: {content}")  # Result: [1, 2, 3]


@job(
    config=region,
    resource_defs={
        "wandb_config": make_values_resource(
            entity=str,
            project=str,
        ),
        "wandb_resource": wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}}),
        "io_manager": wandb_artifacts_io_manager,
    },
)
def partitioned_job_example() -> None:
    """Example of a simple job that writes and reads a partitioned Artifact."""
    read_partitioned_artifact(write_partitioned_artifact())
