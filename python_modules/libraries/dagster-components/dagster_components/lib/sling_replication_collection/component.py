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
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import registered_component_type
from dagster_components.core.component_scaffolder import ComponentScaffolder
from dagster_components.core.schema.base import Resolver, resolver
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecModel,
    ResolvableModel,
)
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


@record
class SlingReplicationSpec:
    path: str
    op: Optional[OpSpecModel]
    translator: Optional[DagsterSlingTranslator]


class SlingReplicationParams(ResolvableModel):
    path: str
    op: Optional[OpSpecModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel],
        ResolvableFieldInfo(required_scope={"stream_definition"}),
    ] = None


class SlingReplicationCollectionParams(ResolvableModel):
    sling: SlingResource
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@resolver(
    fromtype=SlingReplicationParams,
    totype=SlingReplicationSpec,
    exclude_fields={"asset_attributes"},
    additional_fields={"translator"},
)
class SlingReplicationResolver(Resolver):
    def resolve_translator(self, resolver: ResolutionContext) -> DagsterSlingTranslator:
        return get_wrapped_translator_class(DagsterSlingTranslator)(
            resolving_info=ResolvingInfo(
                "stream_definition",
                self.model.asset_attributes or AssetAttributesModel(),
                resolver,
            ),
        )


@resolver(fromtype=SlingReplicationCollectionParams)
class SlingReplicationCollectionResolver(Resolver[SlingReplicationCollectionParams]):
    def resolve_sling(self, resolver: ResolutionContext) -> SlingResource:
        return SlingResource(**resolver.resolve_value(self.model.sling.model_dump()))

    def resolve_replications(self, resolver: ResolutionContext) -> Sequence[SlingReplicationSpec]:
        return [resolver.resolve_value(replication) for replication in self.model.replications]

    def resolve_transforms(
        self, resolver: ResolutionContext
    ) -> Optional[Sequence[Callable[[Definitions], Definitions]]]:
        return (
            [resolver.resolve_value(transform) for transform in self.model.transforms]
            if self.model.transforms
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

    @classmethod
    def load(cls, params: SlingReplicationCollectionParams, context: ComponentLoadContext) -> Self:
        return params.resolve_as(cls, context.resolution_context)

    def build_asset(
        self, context: ComponentLoadContext, replication_spec: SlingReplicationSpec
    ) -> AssetsDefinition:
        op_spec = replication_spec.op or OpSpecModel()

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
