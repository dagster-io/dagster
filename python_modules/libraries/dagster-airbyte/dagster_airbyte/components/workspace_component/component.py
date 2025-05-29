from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._core.definitions.job_definition import default_job_io_manager
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils import TranslatorResolvingInfo
from dagster_shared import check
from typing_extensions import TypeAlias

from dagster_airbyte.asset_defs import build_airbyte_assets_definitions
from dagster_airbyte.components.workspace_component.scaffolder import (
    AirbyteCloudWorkspaceComponentScaffolder,
)
from dagster_airbyte.resources import AirbyteCloudWorkspace
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteConnectionTableProps,
    DagsterAirbyteTranslator,
)


def resolve_translation(context: dg.ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "props",
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, props: info.get_asset_spec(
        base_asset_spec,
        {
            "props": props,
            "spec": base_asset_spec,
        },
    )


TranslationFn: TypeAlias = Callable[[dg.AssetSpec, AirbyteConnectionTableProps], dg.AssetSpec]
ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    dg.Resolver(
        resolve_translation,
        model_field_type=Union[str, dg.AssetAttributesModel],
    ),
]


class ProxyDagsterAirbyteTranslator(DagsterAirbyteTranslator):
    def __init__(self, fn: TranslationFn):
        self.fn = fn

    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        spec = self.fn(base_asset_spec, props)

        return spec


class AirbyteCloudWorkspaceModel(dg.Model):
    workspace_id: Annotated[str, pydantic.Field(..., description="The Airbyte Cloud workspace ID.")]
    client_id: Annotated[
        str, pydantic.Field(..., description="Client ID used to authenticate to Airbyte Cloud.")
    ]
    client_secret: Annotated[
        str, pydantic.Field(..., description="Client secret used to authenticate to Airbyte Cloud.")
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


@dg.scaffold_with(AirbyteCloudWorkspaceComponentScaffolder)
class AirbyteCloudWorkspaceComponent(dg.Component, dg.Model, dg.Resolvable):
    """Loads Airbyte Cloud connections from a given Airbyte Cloud workspace as Dagster assets.
    Materializing these assets will trigger a sync of the Airbyte Cloud connection, enabling
    you to schedule Airbyte Cloud syncs using Dagster.
    """

    workspace: Annotated[
        AirbyteCloudWorkspace,
        dg.Resolver(
            lambda context, model: AirbyteCloudWorkspace(
                **resolve_fields(model, AirbyteCloudWorkspace, context)  # type: ignore
            )
        ),
    ]
    connection_selector: Annotated[
        Optional[Callable[[AirbyteConnection], bool]],
        dg.Resolver(
            resolve_connection_selector,
            model_field_type=Union[
                str, AirbyteConnectionSelectorByName, AirbyteConnectionSelectorById
            ],
            description="Function used to select Airbyte Cloud connections to pull into Dagster.",
        ),
    ] = None
    translation: Optional[ResolvedTranslationFn] = pydantic.Field(
        None,
        description="Function used to translate Airbyte Cloud connection table properties into Dagster asset specs.",
    )

    @cached_property
    def workspace_resource(self) -> AirbyteCloudWorkspace:
        return self.workspace

    @cached_property
    def translator(self) -> DagsterAirbyteTranslator:
        if self.translation:
            return ProxyDagsterAirbyteTranslator(self.translation)
        return DagsterAirbyteTranslator()

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        airbyte_assets = build_airbyte_assets_definitions(
            workspace=self.workspace_resource,
            dagster_airbyte_translator=self.translator,
            connection_selector_fn=self.connection_selector,
        )
        assets_with_resource = [
            airbyte_asset.with_resources(
                {
                    "airbyte": self.workspace_resource.get_resource_definition(),
                    "io_manager": default_job_io_manager,
                }
            )
            for airbyte_asset in airbyte_assets
        ]
        return dg.Definitions(assets=assets_with_resource)
