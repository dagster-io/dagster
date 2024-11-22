from typing import Tuple

import wandb
from dagster import AssetOut, multi_asset


@multi_asset(
    name="write_multiple_artifacts",
    compute_kind="wandb",
    outs={
        "first_table": AssetOut(
            metadata={
                "wandb_artifact_configuration": {
                    "type": "training_dataset",
                }
            },
        ),
        "second_table": AssetOut(
            metadata={
                "wandb_artifact_configuration": {
                    "type": "validation_dataset",
                }
            },
        ),
    },
    group_name="my_multi_asset_group",
)
def write_multiple_artifacts() -> tuple[wandb.Table, wandb.Table]:
    """Example writing multiple W&B Artifact with @multi_asset.

    Returns:
        - wandb.Table: our training dataset
        - wandb.Table: our validation dataset

    Both outputs will be turned into a W&B Artifact. They don't need to be of the same type.
    """
    first_table = wandb.Table(columns=["a", "b", "c"], data=[[1, 2, 3]])
    second_table = wandb.Table(columns=["d", "e"], data=[[4, 5]])

    return first_table, second_table
