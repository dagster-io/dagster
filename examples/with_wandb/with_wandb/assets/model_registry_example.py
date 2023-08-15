import wandb
from dagster import AssetIn, Config, asset
from wandb import Artifact

MODEL_NAME = "my_model"


@asset(
    name=MODEL_NAME,
    compute_kind="wandb",
)
def write_model() -> Artifact:
    """Write your model.

    Here, we have we're creating a very simple Artifact with the integration.

    In a real scenario this would be more complex.

    Returns:
        wandb.Artifact: Our model
    """
    return wandb.Artifact(MODEL_NAME, "model")


class PromoteBestModelToProductionConfig(Config):
    model_registry: str


@asset(
    compute_kind="wandb",
    name="registered-model",
    ins={"artifact": AssetIn(key=MODEL_NAME)},
    output_required=False,
)
def promote_best_model_to_production(
    artifact: Artifact,
    config: PromoteBestModelToProductionConfig,
):
    """Example that links a model stored in a W&B Artifact to the Model Registry.

    Args:
        context (AssetExecutionContext): Dagster execution context
        artifact (wandb.wandb_sdk.wandb_artifacts.Artifact): Downloaded Artifact object
    """
    # In a real scenario you would evaluate model performance
    performance_is_better = True  # for simplicity we always promote the new model
    if performance_is_better:
        model_registry = config.model_registry
        # promote the model to production
        artifact.link(target_path=model_registry, aliases=["production"])
