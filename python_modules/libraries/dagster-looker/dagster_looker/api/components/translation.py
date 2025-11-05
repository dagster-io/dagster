"""Translation utilities for Looker components."""

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

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerStructureType,
)

LookerTranslationFn: TypeAlias = TranslationFn[LookerApiTranslatorStructureData]

ResolvedTargetedLookerTranslationFn = Annotated[
    LookerTranslationFn,
    TranslationFnResolver[LookerApiTranslatorStructureData](lambda data: {"data": data}),
]


@record
class LookerAssetArgs(AssetSpecUpdateKwargs, Resolvable):
    for_view: Optional[ResolvedTargetedLookerTranslationFn] = None
    for_explore: Optional[ResolvedTargetedLookerTranslationFn] = None
    for_dashboard: Optional[ResolvedTargetedLookerTranslationFn] = None


def resolve_multilayer_translation(context: ResolutionContext, model):
    """The Looker translation schema supports defining global transforms
    as well as per-content-type transforms. This resolver composes the
    per-content-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: LookerApiTranslatorStructureData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=LookerAssetArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_view = nested_translation_fns.get("for_view")
        for_explore = nested_translation_fns.get("for_explore")
        for_dashboard = nested_translation_fns.get("for_dashboard")

        if data.structure_type == LookerStructureType.VIEW and for_view:
            return for_view(processed_spec, data)
        if data.structure_type == LookerStructureType.EXPLORE and for_explore:
            return for_explore(processed_spec, data)
        if data.structure_type == LookerStructureType.DASHBOARD and for_dashboard:
            return for_dashboard(processed_spec, data)

        return processed_spec

    return _translation_fn


ResolvedMultilayerTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_multilayer_translation,
        model_field_type=Union[str, LookerAssetArgs.model()],
    ),
]


def create_looker_component_translator(component_cls):
    """Creates a translator class for a Looker component."""

    class LookerComponentTranslator(
        create_component_translator_cls(component_cls, DagsterLookerApiTranslator),
        ComponentTranslator[component_cls],
    ):
        def __init__(self, component):
            self._component = component

        def get_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
            base_asset_spec = super().get_asset_spec(looker_structure)
            if self.component.translation is None:
                return base_asset_spec
            else:
                return self.component.translation(base_asset_spec, looker_structure)

    return LookerComponentTranslator
