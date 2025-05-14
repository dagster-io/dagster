from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, Optional, Union

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster.components import Resolvable, Resolver
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel, AssetPostProcessor, OpSpec
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils import TranslatorResolvingInfo
from typing_extensions import TypeAlias

from dagster_sling.asset_decorator import sling_assets
from dagster_sling.components.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import AssetExecutionContext, SlingResource

SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


def resolve_translation(context: ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "stream_definition",
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, stream_definition: info.get_asset_spec(
        base_asset_spec,
        {
            "stream_definition": stream_definition,
            "spec": base_asset_spec,
        },
    )


TranslationFn: TypeAlias = Callable[[AssetSpec, Mapping[str, Any]], AssetSpec]

ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_translation,
        model_field_type=Union[str, AssetAttributesModel],
    ),
]


class ProxyDagsterSlingTranslator(DagsterSlingTranslator):
    def __init__(self, fn: TranslationFn):
        self._fn = fn

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        base_asset_spec = super().get_asset_spec(stream_definition)
        return self._fn(base_asset_spec, stream_definition)


@dataclass
class SlingReplicationSpecModel(Resolvable):
    path: str
    op: Optional[OpSpec] = None
    translation: Optional[ResolvedTranslationFn] = None
    include_metadata: list[SlingMetadataAddons] = field(default_factory=list)

    @cached_property
    def translator(self):
        if self.translation:
            return ProxyDagsterSlingTranslator(self.translation)
        return DagsterSlingTranslator()


def resolve_resource(
    context: ResolutionContext,
    sling,
) -> SlingResource:
    return SlingResource(**context.resolve_value(sling.model_dump())) if sling else SlingResource()


@scaffold_with(SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component, Resolvable):
    """Expose one or more Sling replications to Dagster as assets.

    [Sling](https://slingdata.io/) is a Powerful Data Integration tool enabling seamless ELT
    operations as well as quality checks across files, databases, and storage systems.

    dg scaffold dagster_sling.SlingReplicationCollectionComponent {component_path} to get started.

    This will create a component.yaml as well as a `replication.yaml` which is a Sling-specific configuration
    file. See Sling's [documentation](https://docs.slingdata.io/concepts/replication#overview) on `replication.yaml`.
    """

    resource: Annotated[
        SlingResource,
        Resolver(
            resolve_resource,
            model_field_name="sling",
        ),
    ] = field(default_factory=SlingResource)
    replications: Sequence[SlingReplicationSpecModel] = field(default_factory=list)
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def build_asset(
        self, context: ComponentLoadContext, replication_spec_model: SlingReplicationSpecModel
    ) -> AssetsDefinition:
        op_spec = replication_spec_model.op or OpSpec()

        @sling_assets(
            name=op_spec.name or Path(replication_spec_model.path).stem,
            op_tags=op_spec.tags,
            replication_config=context.path / replication_spec_model.path,
            dagster_sling_translator=replication_spec_model.translator,
            backfill_policy=op_spec.backfill_policy,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(
                context=context, sling=self.resource, replication_spec_model=replication_spec_model
            )

        return _asset

    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        iterator = sling.replicate(context=context)
        if "column_metadata" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_row_count()
        yield from iterator

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = Definitions(
            assets=[self.build_asset(context, replication) for replication in self.replications],
        )
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs
