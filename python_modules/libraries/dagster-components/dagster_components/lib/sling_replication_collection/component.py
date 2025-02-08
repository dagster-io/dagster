from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster._record import record
from dagster_sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_sling.resources import AssetExecutionContext

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import registered_component_type
from dagster_components.core.component_scaffolder import ComponentScaffolder
from dagster_components.core.resolution_engine.context import ResolutionContext
from dagster_components.core.resolution_engine.resolver import Resolver, resolver
from dagster_components.core.schema.metadata import SchemaFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetSpecTransformSchema,
    ComponentSchema,
    OpSpecSchema,
)
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


@record
class SlingReplicationSpec:
    path: str
    op: Optional[OpSpecSchema]
    translator: Optional[DagsterSlingTranslator]


class SlingReplicationParams(ComponentSchema):
    path: str
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        SchemaFieldInfo(required_scope={"stream_definition"}),
    ] = None


class SlingReplicationCollectionParams(ComponentSchema):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformSchema]] = None


@resolver(
    fromtype=SlingReplicationParams,
    totype=SlingReplicationSpec,
    exclude_fields={"asset_attributes"},
)
class SlingReplicationResolver(Resolver):
    def resolve_translator(self, resolver: ResolutionContext) -> DagsterSlingTranslator:
        return get_wrapped_translator_class(DagsterSlingTranslator)(
            resolving_info=TranslatorResolvingInfo(
                "stream_definition",
                self.schema.asset_attributes or AssetAttributesSchema(),
                resolver,
            ),
        )


@resolver(fromtype=SlingReplicationCollectionParams)
class SlingReplicationCollectionResolver(Resolver[SlingReplicationCollectionParams]):
    def resolve_sling(self, resolver: ResolutionContext) -> SlingResource:
        return (
            SlingResource(**resolver.resolve_value(self.schema.sling.model_dump()))
            if self.schema.sling
            else SlingResource()
        )

    def resolve_replications(self, resolver: ResolutionContext) -> Sequence[SlingReplicationSpec]:
        return [resolver.resolve_value(replication) for replication in self.schema.replications]

    def resolve_transforms(
        self, resolver: ResolutionContext
    ) -> Optional[Sequence[Callable[[Definitions], Definitions]]]:
        return (
            [resolver.resolve_value(transform) for transform in self.schema.transforms]
            if self.schema.transforms
            else None
        )


@registered_component_type
class SlingReplicationCollection(Component):
    """Expose one or more Sling replications to Dagster as assets."""

    def __init__(
        self,
        sling: SlingResource,
        replications: Sequence[SlingReplicationSpec],
        transforms: Optional[Sequence[Callable[[Definitions], Definitions]]] = None,
    ):
        self.resource = sling
        self.replications = replications
        self.transforms = transforms or []

    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        from dagster_components.lib.sling_replication_collection.scaffolder import (
            SlingReplicationComponentScaffolder,
        )

        return SlingReplicationComponentScaffolder()

    @classmethod
    def get_schema(cls) -> type[SlingReplicationCollectionParams]:
        return SlingReplicationCollectionParams

    def build_asset(
        self, context: ComponentLoadContext, replication_spec: SlingReplicationSpec
    ) -> AssetsDefinition:
        op_spec = replication_spec.op or OpSpecSchema()

        @sling_assets(
            name=op_spec.name or Path(replication_spec.path).stem,
            op_tags=op_spec.tags,
            replication_config=context.path / replication_spec.path,
            dagster_sling_translator=replication_spec.translator,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(context=context, sling=self.resource)

        return _asset

    def execute(
        self, context: AssetExecutionContext, sling: SlingResource
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        yield from sling.replicate(context=context)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = Definitions(
            assets=[self.build_asset(context, replication) for replication in self.replications],
        )
        for transform in self.transforms:
            defs = transform(defs)
        return defs
