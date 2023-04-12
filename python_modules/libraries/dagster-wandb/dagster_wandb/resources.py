from typing import Any, Dict

import wandb
from dagster import ConfigurableResource, InitResourceContext, resource
from pydantic import Field
from wandb.sdk.internal.internal_api import Api

WANDB_CLOUD_HOST: str = "https://api.wandb.ai"


class WandBResource(ConfigurableResource):
    """Dagster resource used to communicate with the W&B API. It's useful when you want to use the
    wandb client within your ops and assets. It's a required resources if you are using the W&B IO
    Manager.

    It automatically authenticates using the provided API key.

    For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    **Example:**

    .. code-block:: python

        from dagster import EnvVar, job
        from dagster_wandb import WandBResource

        @op
        def my_wandb_op(wandb_resource: WandBResource):
            wandb_resource.get_api()

        @job
        def my_wandb_job():
            my_wandb_op()

        defs = Definitions(
            jobs=[my_wandb_job],
            resources={
                "wandb_resource": WandBResource(api_key=EnvVar("WANDB_API_KEY")),
            },
        )

    """

    api_key: str = Field(
        description="W&B API key necessary to communicate with the W&B API.",
    )
    host: str = Field(
        default=WANDB_CLOUD_HOST,
        description="API host server you wish to use. Only required if you are using W&B Server.",
    )

    def login(self):
        wandb.login(
            key=self.api_key,
            host=self.host,
            anonymous="never",
        )

    def get_api(self) -> Api:
        client_settings = wandb.Settings(
            api_key=self.api_key,
            base_url=self.host,
            anonymous="never",
            launch=True,
        )
        return Api(default_settings=client_settings, load_settings=False)

    # api_key = context.resource_config["api_key"]
    # host = context.resource_config["host"]
    # wandb.login(
    #     key=api_key,
    #     host=host,
    #     anonymous="never",
    # )
    # client_settings = wandb.Settings(
    #     api_key=api_key,
    #     base_url=host,
    #     anonymous="never",
    #     launch=True,
    # )
    # api = Api(default_settings=client_settings, load_settings=False)

    def get_host(self) -> str:
        return self.host


@resource(
    config_schema=WandBResource.to_config_schema(),
    description="Resource for interacting with Weights & Biases",
)
def wandb_resource(context: InitResourceContext) -> Dict[str, Any]:
    """Dagster resource used to communicate with the W&B API. It's useful when you want to use the
    wandb client within your ops and assets. It's a required resources if you are using the W&B IO
    Manager.

    It automatically authenticates using the provided API key.

    For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    **Example:**

    .. code-block:: python

        from dagster import job
        from dagster_wandb import wandb_resource

        my_wandb_resource = wandb_resource.configured({"api_key": {"env": "WANDB_API_KEY"}})

        @job(resource_defs={"wandb_resource": my_wandb_resource})
        def my_wandb_job():
            ...

    """
    _wandb_resource = WandBResource.from_resource_context(context)
    _wandb_resource.login()

    return {
        "sdk": wandb,
        "api": _wandb_resource.get_api(),
        "host": _wandb_resource.get_host(),
    }
