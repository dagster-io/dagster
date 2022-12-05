from typing import Any, Dict

import wandb
from wandb.sdk.internal.internal_api import Api

from dagster import Field, InitResourceContext, String, StringSource, resource

WANDB_CLOUD_HOST: str = "https://api.wandb.ai"


@resource(
    config_schema={
        "api_key": Field(StringSource, description="Weights & Biases API key", is_required=True),
        "host": Field(
            String,
            description="The Weights & Biases host server to connect to",
            is_required=False,
            default_value=WANDB_CLOUD_HOST,
        ),
    },
    description="Resource for interacting with Weights & Biases",
)
def wandb_resource(context: InitResourceContext) -> Dict[str, Any]:
    """Resource for interacting with Weights & Biases."""
    api_key = context.resource_config["api_key"]
    host = context.resource_config["host"]
    wandb.login(
        key=api_key,
        host=host,
        anonymous="never",
    )
    client_settings = wandb.Settings(
        api_key=api_key,
        base_url=host,
        anonymous="never",
        launch=True,
    )
    api = Api(default_settings=client_settings, load_settings=False)
    return {"sdk": wandb, "api": api, "host": host}
