"""Translation utilities for Tableau components."""

from typing import Annotated, Optional, TypeAlias, Union

from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster.components import Resolvable, Resolver
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetSpecUpdateKwargs
from dagster.components.utils import TranslatorResolvingInfo
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared.record import record

from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauContentType,
    TableauTranslatorData,
)

TableauTranslationFn: TypeAlias = TranslationFn[TableauTranslatorData]

ResolvedTargetedTableauTranslationFn = Annotated[
    TableauTranslationFn,
    TranslationFnResolver[TableauTranslatorData](lambda data: {"data": data}),
]


@record
class TableauAssetArgs(AssetSpecUpdateKwargs, Resolvable):
    for_sheet: Optional[ResolvedTargetedTableauTranslationFn] = None
    for_dashboard: Optional[ResolvedTargetedTableauTranslationFn] = None
    for_data_source: Optional[ResolvedTargetedTableauTranslationFn] = None


def resolve_multilayer_translation(context: ResolutionContext, model):
    """The Tableau translation schema supports defining global transforms
    as well as per-content-type transforms. This resolver composes the
    per-content-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: TableauTranslatorData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=TableauAssetArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_sheet = nested_translation_fns.get("for_sheet")
        for_dashboard = nested_translation_fns.get("for_dashboard")
        for_data_source = nested_translation_fns.get("for_data_source")

        if data.content_type == TableauContentType.SHEET and for_sheet:
            return for_sheet(processed_spec, data)
        if data.content_type == TableauContentType.DASHBOARD and for_dashboard:
            return for_dashboard(processed_spec, data)
        if data.content_type == TableauContentType.DATA_SOURCE and for_data_source:
            return for_data_source(processed_spec, data)

        return processed_spec

    return _translation_fn


ResolvedMultilayerTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_multilayer_translation,
        model_field_type=Union[str, TableauAssetArgs.model()],
    ),
]


def create_tableau_component_translator(component_cls):
    """Creates a translator class for a Tableau component."""

    class TableauComponentTranslator(
        create_component_translator_cls(component_cls, DagsterTableauTranslator),
        ComponentTranslator[component_cls],
    ):
        def __init__(self, component):
            self._component = component

        def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
            base_asset_spec = super().get_asset_spec(data)
            if self.component.translation is None:
                return base_asset_spec
            else:
                return self.component.translation(base_asset_spec, data)

    return TableauComponentTranslator
