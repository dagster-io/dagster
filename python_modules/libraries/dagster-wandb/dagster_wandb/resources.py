from typing import Any

import wandb
from dagster import Field, InitResourceContext, String, StringSource, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from wandb.sdk.internal.internal_api import Api

WANDB_CLOUD_HOST: str = "https://api.wandb.ai"


@dagster_maintained_resource
@resource(
    config_schema={
        "api_key": Field(
            StringSource,
            description="W&B API key necessary to communicate with the W&B API.",
            is_required=True,
        ),
        "host": Field(
            String,
            description=(
                "API host server you wish to use. Only required if you are using W&B Server."
            ),
            is_required=False,
            default_value=WANDB_CLOUD_HOST,
        ),
    },
    description="Resource for interacting with Weights & Biases",
)
def wandb_resource(context: InitResourceContext) -> dict[str, Any]:
    """Dagster resource used to communicate with the W&B API. It's useful when you want to use the
    wandb client within your ops and assets. It's a required resources if you are using the W&B IO
    Manager.

    It automatically authenticates using the provided API key.

    For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_.

    To configure this resource, we recommend using the `configured
    <https://legacy-docs.dagster.io/concepts/configuration/configured>`_ method.

    **Example:**

    .. code-block:: python

        from dagster import job
        from dagster_wandb import wandb_resource

        my_wandb_resource = wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}})

        @job(resource_defs={"wandb_resource": my_wandb_resource})
        def my_wandb_job():
            ...

    """
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
