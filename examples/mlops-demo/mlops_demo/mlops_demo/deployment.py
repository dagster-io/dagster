import polars as pl
import dagster as dg
from sklearn.ensemble import RandomForestClassifier
import pickle
from datetime import datetime


@dg.asset(
    description="Production model candidates",
    group_name="deployment",
    automation_condition=dg.AutomationCondition.eager()
)
def production_model_candidates(context: dg.AssetExecutionContext, trained_model: RandomForestClassifier) -> list[str]:

    model_name = f"trained-models/model-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pickle"
    pickle.dump(trained_model, open(model_name, "wb+"))

    with open("trained-models/list-of-models.txt", "a+") as f:
        f.write(model_name + "\n")

    with open("trained-models/list-of-models.txt", "r") as f:
        models = f.read().splitlines()

    context.add_asset_metadata({
        "list-of-models": models
    })

    return models

class DeployedModelConfiguration(dg.Config):
    model_name: str

@dg.asset(
    description="The currently deployed model",
    group_name="deployment"
)
def deployed_model(production_model_candidates: list[str], config: DeployedModelConfiguration) -> RandomForestClassifier:

    if config.model_name not in production_model_candidates:
        raise dg.Failure("The requested model does not exist")
    
    with open(config.model_name, "rb") as f:
        model: RandomForestClassifier = pickle.load(f)

    return model