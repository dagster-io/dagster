from typing import Any, Dict, Literal, Optional

from dagster import AssetExecutionContext
from dagster._core.blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster._model.pydantic_compat_layer import USING_PYDANTIC_2
from pydantic import ConfigDict, Field

from dagster_embedded_elt.sling.asset_decorator import sling_assets
from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource


class SlingResourceBlueprint(Blueprint):
    """Blueprint which creates a Dagster resource that holds a collection of Sling connections.

    Templated after the Sling environment file, see the Sling documentation for more information.
    https://docs.slingdata.io/sling-cli/environment.
    """

    type: Literal["dagster_embedded_elt/sling_resource"] = "dagster_embedded_elt/sling_resource"
    dagster_resource_name: str = Field(
        "sling",
        description="The name of the Dagster resource that will be created to hold the connections.",
    )
    connections: Dict[str, Any] = Field(
        ..., description="A dictionary of connection configurations."
    )
    variables: Optional[Dict[str, Any]] = Field(
        default=None,
        description="A dictionary of variables which can be used in the connection configs.",
    )

    def build_defs(self) -> BlueprintDefinitions:
        for name, connection_details in self.connections.items():
            if "type" not in connection_details:
                raise ValueError(
                    f"Connection details for connection '{name}' must include a 'type'."
                )

        connections = [
            SlingConnectionResource(name=key, **value) for key, value in self.connections.items()
        ]
        return BlueprintDefinitions(
            resources={self.dagster_resource_name: SlingResource(connections=connections)}
        )


class SlingSyncBlueprint(Blueprint):
    """Blueprint which creates a Dagster asset for one or more Sling replication configurations.

    Follows the schema of the Sling replication file, see the Sling documentation for more information.
    https://docs.slingdata.io/sling-cli/run/configuration/replication
    """

    # Ensures that other fields can be passed in, even if they are not explicitly defined
    if USING_PYDANTIC_2:
        model_config = ConfigDict(extra="allow")  # type: ignore
    else:

        class Config:
            extra = "allow"

    type: Literal["dagster_embedded_elt/sling_assets"] = "dagster_embedded_elt/sling_assets"
    dagster_op_name: str = Field(
        ...,
        description="The name of the underlying Dagster op to create.",
    )

    def build_defs(self) -> BlueprintDefinitions:
        replication_config = {**dict(self)}
        del replication_config["dagster_op_name"]
        del replication_config["type"]

        @sling_assets(replication_config=replication_config, name=self.dagster_op_name)
        def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
            yield from sling.replicate(context=context)

        return BlueprintDefinitions(assets=[my_sling_assets])
