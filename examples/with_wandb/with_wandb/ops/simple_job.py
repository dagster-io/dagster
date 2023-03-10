from typing import List

from dagster import In, Out, job, make_values_resource, op
from dagster_wandb import wandb_artifacts_io_manager, wandb_resource

MY_FIRST_LIST = "my_first_list"


@op(
    out=Out(
        metadata={
            "wandb_artifact_configuration": {
                "name": MY_FIRST_LIST,
                "type": "dataset",
            }
        }
    )
)
def create_my_first_list() -> List[int]:
    """Example writing a simple Python list into an W&B Artifact.

    The list is pickled in the Artifact. We can configure the Artifact name and type with the
    metadata object.

    Returns:
        List[int]: The list we want to store in an Artifact
    """
    return [1, 2, 3]


@op(
    ins={
        "downloaded_artifact": In(
            metadata={
                "wandb_artifact_configuration": {
                    "name": MY_FIRST_LIST,
                }
            }
        )
    },
    out=Out(
        metadata={
            "wandb_artifact_configuration": {
                "name": "my_final_list",
                "type": "dataset",
            }
        }
    ),
)
def create_my_final_list(downloaded_artifact: List[int]) -> List[int]:
    """Example downloading an Artifact and creating a new one.

    Args:
        my_first_list (List[int]): Unpickled content of Artifact created in the previous asset

    Returns:
        List[int]: The content of the new Artifact.

    my_first_list is unpickled from the Artifact. We then concatene that list with another one into
    a new Artifact.
    """
    return downloaded_artifact + [4, 5, 7]


@job(
    resource_defs={
        "wandb_config": make_values_resource(
            entity=str,
            project=str,
        ),
        "wandb_resource": wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}}),
        "io_manager": wandb_artifacts_io_manager.configured(
            {"wandb_run_id": "my_resumable_run_id"}
        ),
    }
)
def simple_job_example():
    """Example of a simple job using the Artifact integration."""
    create_my_final_list(create_my_first_list())
