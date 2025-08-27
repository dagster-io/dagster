from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._core.definitions.job_definition import default_job_io_manager
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared import check

from dagster_fivetran.asset_defs import build_fivetran_assets_definitions
from dagster_fivetran.components.workspace_component.scaffolder import (
    FivetranAccountComponentScaffolder,
)
from dagster_fivetran.resources import FivetranWorkspace
from dagster_fivetran.translator import (
    DagsterFivetranTranslator,
    FivetranConnector,
    FivetranConnectorTableProps,
)


class ProxyDagsterFivetranTranslator(DagsterFivetranTranslator):
    def __init__(self, fn: TranslationFn[FivetranConnectorTableProps]):
        self.fn = fn

    def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        spec = self.fn(base_asset_spec, props)

        return spec


class FivetranWorkspaceModel(pydantic.BaseModel):
    account_id: str = pydantic.Field(..., description="The Fivetran account ID.")
    api_key: str = pydantic.Field(
        ..., description="API key used to authenticate to a Fivetran instance."
    )
    api_secret: str = pydantic.Field(
        ..., description="API secret used to authenticate to a Fivetran instance."
    )


class FivetranConnectorSelectorByName(pydantic.BaseModel):
    by_name: Sequence[str] = pydantic.Field(
        ...,
        description="A list of connector names to include in the collection.",
    )


class FivetranConnectorSelectorById(pydantic.BaseModel):
    by_id: Sequence[str] = pydantic.Field(
        ...,
        description="A list of connector IDs to include in the collection.",
    )


def resolve_connector_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[FivetranConnector], bool]]:
    if isinstance(model, str):
        model = context.resolve_value(model)

    if isinstance(model, FivetranConnectorSelectorByName):
        return lambda connector: connector.name in model.by_name
    elif isinstance(model, FivetranConnectorSelectorById):
        return lambda connector: connector.id in model.by_id
    else:
        check.failed(f"Unknown connector target type: {type(model)}")


@dg.scaffold_with(FivetranAccountComponentScaffolder)
class FivetranAccountComponent(dg.Component, dg.Model, dg.Resolvable):
    """Loads Fivetran connectors from a given Fivetran instance as Dagster assets.
    Materializing these assets will trigger a sync of the Fivetran connector, enabling
    you to schedule Fivetran syncs using Dagster.
    """

    workspace: Annotated[
        FivetranWorkspace,
        dg.Resolver(
            lambda context, model: FivetranWorkspace(
                **resolve_fields(model, FivetranWorkspace, context)
            )
        ),
    ]
    connector_selector: Annotated[
        Optional[Callable[[FivetranConnector], bool]],
        dg.Resolver(
            resolve_connector_selector,
            model_field_type=Union[
                str, FivetranConnectorSelectorByName, FivetranConnectorSelectorById
            ],
        ),
    ] = None
    translation: Optional[
        Annotated[
            TranslationFn[FivetranConnectorTableProps],
            TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"props": data}),
        ]
    ] = pydantic.Field(
        None,
        description="Function used to translate Fivetran connector table properties into Dagster asset specs.",
    )

    @cached_property
    def workspace_resource(self) -> FivetranWorkspace:
        return self.workspace

    @cached_property
    def translator(self) -> DagsterFivetranTranslator:
        if self.translation:
            return ProxyDagsterFivetranTranslator(self.translation)
        return DagsterFivetranTranslator()

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        fivetran_assets = build_fivetran_assets_definitions(
            workspace=self.workspace_resource,
            dagster_fivetran_translator=self.translator,
            connector_selector_fn=self.connector_selector,
        )
        assets_with_resource = [
            fivetran_asset.with_resources(
                {
                    "fivetran": self.workspace_resource.get_resource_definition(),
                    "io_manager": default_job_io_manager,
                }
            )
            for fivetran_asset in fivetran_assets
        ]
        return dg.Definitions(assets=assets_with_resource)
