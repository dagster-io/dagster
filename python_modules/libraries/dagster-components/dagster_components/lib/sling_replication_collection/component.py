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
from pydantic import BaseModel

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import registered_component_type
from dagster_components.core.component_scaffolder import ComponentScaffolder
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetSpecTransformSchema,
    OpSpecSchema,
)
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


@record
class SlingReplicationSpec:
    path: str
    op: Optional[OpSpecSchema]
    translator: Optional[DagsterSlingTranslator]


class SlingReplicationParams(ResolvableSchema[SlingReplicationSpec]):
    path: str
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"stream_definition"}),
    ] = None

    def resolve(self, context: ResolutionContext) -> SlingReplicationSpec:
        return SlingReplicationSpec(
            path=context.resolve_value(self.path, as_type=str),
            op=context.resolve_value(self.op),
            translator=get_wrapped_translator_class(DagsterSlingTranslator)(
                resolving_info=TranslatorResolvingInfo(
                    "stream_definition",
                    self.asset_attributes or AssetAttributesSchema(),
                    context,
                ),
            ),
        )


class ResolvedSlingReplicationCollectionSchema(BaseModel):
    sling: SlingResource
    replications: Sequence[SlingReplicationSpec]
    transforms: Sequence[Callable[[Definitions], Definitions]]


class SlingReplicationCollectionParams(ResolvableSchema[ResolvedSlingReplicationCollectionSchema]):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformSchema]] = None

    def resolve(self, context: ResolutionContext) -> ResolvedSlingReplicationCollectionSchema:
        return ResolvedSlingReplicationCollectionSchema(
            sling=SlingResource(**context.resolve_value(self.sling.model_dump()))
            if self.sling
            else SlingResource(),
            replications=context.resolve_value(self.replications),
            transforms=context.resolve_value(self.transforms or []),
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

    @classmethod
    def load(
        cls, context: ComponentLoadContext, schema: SlingReplicationCollectionParams
    ) -> "SlingReplicationCollection":
        resolved = context.resolution_context.resolve_value(schema)
        return cls(
            sling=resolved.sling,
            replications=resolved.replications,
            transforms=resolved.transforms,
        )

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
