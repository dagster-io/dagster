from typing import List

from dagster import AssetIn, asset


@asset(
    name="my_first_list",
    compute_kind="wandb",
    metadata={
        "wandb_artifact_configuration": {
            "type": "dataset",
        }
    },
)
def create_my_first_list() -> list[int]:
    """Example writing a simple Python list into a W&B Artifact.

    The list is pickled in the Artifact. We configure the Artifact type with the
    metadata object.

    Returns:
        List[int]: The list we want to store in an Artifact
    """
    return [1, 2, 3]


@asset(
    name="my_final_list",
    compute_kind="wandb",
    ins={"my_first_list": AssetIn()},
    metadata={
        "wandb_artifact_configuration": {
            "type": "dataset",
        }
    },
)
def create_my_final_list(my_first_list: list[int]) -> list[int]:
    """Example downloading an Artifact and creating a new one.

    Args:
        my_first_list (List[int]): Unpickled content of Artifact created in the previous asset

    Returns:
        List[int]: The content of the new Artifact.

    my_first_list is unpickled from the Artifact. We then concatene that list with another one into
    a new Artifact.
    """
    return my_first_list + [4, 5, 7]
