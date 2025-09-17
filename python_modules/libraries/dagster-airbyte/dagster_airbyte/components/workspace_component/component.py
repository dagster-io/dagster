from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import superseded
from dagster._core.definitions.job_definition import default_job_io_manager
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared import check

from dagster_airbyte.asset_defs import build_airbyte_assets_definitions
from dagster_airbyte.components.workspace_component.scaffolder import (
    AirbyteWorkspaceComponentScaffolder,
)
from dagster_airbyte.resources import AirbyteCloudWorkspace, AirbyteWorkspace
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteConnectionTableProps,
    DagsterAirbyteTranslator,
)


class ProxyDagsterAirbyteTranslator(DagsterAirbyteTranslator):
    def __init__(self, fn: TranslationFn[AirbyteConnectionTableProps]):
        self.fn = fn

    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        spec = self.fn(base_asset_spec, props)

        return spec


class BaseAirbyteWorkspaceModel(dg.Model, dg.Resolvable):
    request_max_retries: Annotated[
        int,
        pydantic.Field(
            default=3,
            description=(
                "The maximum number of times requests to the Airbyte API should be retried "
                "before failing."
            ),
        ),
    ]
    request_retry_delay: Annotated[
        float,
        pydantic.Field(
            default=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
    ]
    request_timeout: Annotated[
        int,
        pydantic.Field(
            default=15,
            description="Time (in seconds) after which the requests to Airbyte are declared timed out.",
        ),
    ]


class AirbyteWorkspaceModel(BaseAirbyteWorkspaceModel):
    rest_api_base_url: Annotated[
        str,
        pydantic.Field(
            ...,
            description=(
                "The base URL for the Airbyte REST API. "
                "For Airbyte Cloud, leave this as the default. "
                "For self-managed Airbyte, this is usually <your Airbyte host>/api/public/v1."
            ),
            examples=[
                "http://localhost:8000/api/public/v1",
                "https://my-airbyte-server.com/api/public/v1",
                "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/public/v1",
            ],
        ),
    ]
    configuration_api_base_url: Annotated[
        str,
        pydantic.Field(
            ...,
            description=(
                "The base URL for the Airbyte Configuration API. "
                "For Airbyte Cloud, leave this as the default. "
                "For self-managed Airbyte, this is usually <your Airbyte host>/api/v1."
            ),
            examples=[
                "http://localhost:8000/api/v1",
                "https://my-airbyte-server.com/api/v1",
                "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/v1",
            ],
        ),
    ]
    workspace_id: Annotated[str, pydantic.Field(..., description="The Airbyte workspace ID.")]
    client_id: Annotated[
        Optional[str],
        pydantic.Field(None, description="Client ID used to authenticate to Airbyte."),
    ]
    client_secret: Annotated[
        Optional[str],
        pydantic.Field(None, description="Client secret used to authenticate to Airbyte."),
    ]
    username: Annotated[
        Optional[str],
        pydantic.Field(
            None,
            description="Username used to authenticate to Airbyte. Used for self-managed Airbyte with basic auth.",
        ),
    ]
    password: Annotated[
        Optional[str],
        pydantic.Field(
            None,
            description="Password used to authenticate to Airbyte. Used for self-managed Airbyte with basic auth.",
        ),
    ]


class AirbyteCloudWorkspaceModel(BaseAirbyteWorkspaceModel):
    workspace_id: Annotated[str, pydantic.Field(..., description="The Airbyte workspace ID.")]
    client_id: Annotated[
        Optional[str],
        pydantic.Field(..., description="Client ID used to authenticate to Airbyte."),
    ]
    client_secret: Annotated[
        Optional[str],
        pydantic.Field(..., description="Client secret used to authenticate to Airbyte."),
    ]


class AirbyteConnectionSelectorByName(dg.Model):
    by_name: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of connection names to include in the collection."),
    ]


class AirbyteConnectionSelectorById(dg.Model):
    by_id: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of connection IDs to include in the collection."),
    ]


def resolve_connection_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[AirbyteConnection], bool]]:
    if isinstance(model, str):
        model = context.resolve_value(model)

    if isinstance(model, AirbyteConnectionSelectorByName):
        return lambda connection: connection.name in model.by_name
    elif isinstance(model, AirbyteConnectionSelectorById):
        return lambda connection: connection.id in model.by_id
    else:
        check.failed(f"Unknown connection target type: {type(model)}")


def resolve_airbyte_workspace_type(context: dg.ResolutionContext, model):
    if isinstance(model, AirbyteWorkspaceModel):
        return AirbyteWorkspace(**resolve_fields(model, AirbyteWorkspaceModel, context))
    elif isinstance(model, AirbyteCloudWorkspaceModel):
        return AirbyteCloudWorkspace(**resolve_fields(model, AirbyteCloudWorkspaceModel, context))
    else:
        check.failed(f"Unknown Airbyte workspace type: {type(model)}")


@dg.scaffold_with(AirbyteWorkspaceComponentScaffolder)
class AirbyteWorkspaceComponent(dg.Component, dg.Model, dg.Resolvable):
    """Loads Airbyte connections from a given Airbyte workspace as Dagster assets.
    Materializing these assets will trigger a sync of the Airbyte connection, enabling
    you to schedule Airbyte syncs using Dagster.
    """

    workspace: Annotated[
        Union[AirbyteWorkspace, AirbyteCloudWorkspace],
        dg.Resolver(
            resolve_airbyte_workspace_type,
            model_field_type=Union[AirbyteWorkspaceModel, AirbyteCloudWorkspaceModel],
        ),
    ]
    connection_selector: Annotated[
        Optional[Callable[[AirbyteConnection], bool]],
        dg.Resolver(
            resolve_connection_selector,
            model_field_type=Union[
                str, AirbyteConnectionSelectorByName, AirbyteConnectionSelectorById
            ],
            description="Function used to select Airbyte connections to pull into Dagster.",
        ),
    ] = None
    translation: Optional[
        Annotated[
            TranslationFn[AirbyteConnectionTableProps],
            TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"props": data}),
        ]
    ] = pydantic.Field(
        None,
        description="Function used to translate Airbyte connection table properties into Dagster asset specs.",
    )

    @cached_property
    def translator(self) -> DagsterAirbyteTranslator:
        if self.translation:
            return ProxyDagsterAirbyteTranslator(self.translation)
        return DagsterAirbyteTranslator()

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        airbyte_assets = build_airbyte_assets_definitions(
            workspace=self.workspace,
            dagster_airbyte_translator=self.translator,
            connection_selector_fn=self.connection_selector,
        )
        assets_with_resource = [
            airbyte_asset.with_resources(
                {
                    "airbyte": self.workspace.get_resource_definition(),
                    "io_manager": default_job_io_manager,
                }
            )
            for airbyte_asset in airbyte_assets
        ]
        return dg.Definitions(assets=assets_with_resource)


# Subclassing to create the alias to be able to use the superseded decorator.
@superseded(additional_warn_text="Superseded. Use AirbyteWorkspaceComponent instead.")
class AirbyteCloudWorkspaceComponent(AirbyteWorkspaceComponent): ...
