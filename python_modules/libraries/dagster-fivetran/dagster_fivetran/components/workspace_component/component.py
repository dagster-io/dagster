from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import public
from dagster._utils.names import clean_name
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared import check

from dagster_fivetran.components.workspace_component.scaffolder import (
    FivetranAccountComponentScaffolder,
)
from dagster_fivetran.resources import FivetranWorkspace
from dagster_fivetran.translator import (
    DagsterFivetranTranslator,
    FivetranConnector,
    FivetranConnectorTableProps,
    FivetranMetadataSet,
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


@public
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
    def _translator(self) -> DagsterFivetranTranslator:
        if self.translation:
            return ProxyDagsterFivetranTranslator(self.translation)
        return DagsterFivetranTranslator()

    def execute(
        self, context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
    ) -> Iterable[Union[dg.AssetMaterialization, dg.MaterializeResult]]:
        yield from fivetran.sync_and_poll(context=context)

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # get all specs for the selected connectors and group them by connector
        specs_by_connector_name = defaultdict(list)
        for spec in self.workspace.load_asset_specs(
            dagster_fivetran_translator=self._translator,
            connector_selector_fn=self.connector_selector or (lambda connector: bool(connector)),
        ):
            connector_name = check.not_none(
                FivetranMetadataSet.extract(spec.metadata).connector_name
            )
            specs_by_connector_name[connector_name].append(spec)

        # for each connector, create a subsettable multi-asset
        assets = []
        for connector_name, specs in specs_by_connector_name.items():

            @dg.multi_asset(
                name=f"fivetran_{clean_name(connector_name)}", can_subset=True, specs=specs
            )
            def _asset(context: dg.AssetExecutionContext):
                yield from self.execute(context=context, fivetran=self.workspace)

            assets.append(_asset)

        return dg.Definitions(assets=assets)
