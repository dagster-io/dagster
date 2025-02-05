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
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecModel,
    ResolvableModel,
)
from dagster_components.core.schema.resolver import ResolveContext
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


@record
class SlingReplicationSpec:
    relative_path: str
    op_spec: OpSpecModel
    translator: DagsterSlingTranslator


class SlingReplicationParams(ResolvableModel):
    path: str
    op: Annotated[Optional[OpSpecModel], ResolvableFieldInfo(resolved_field_name="op_spec")] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel],
        ResolvableFieldInfo(required_scope={"stream_definition"}, resolved_field_name="translator"),
    ] = None

    def resolve_translator(self, resolver: ResolveContext) -> DagsterSlingTranslator:
        return get_wrapped_translator_class(DagsterSlingTranslator)(
            resolving_info=ResolvingInfo(
                "stream_definition", self.asset_attributes or AssetAttributesModel(), resolver
            ),
        )

    def resolve(self, context: ResolveContext) -> SlingReplicationSpec:
        return self.resolve_as(SlingReplicationSpec, context)


class SlingReplicationCollectionParams(ResolvableModel):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@registered_component_type
class SlingReplicationCollection(Component):
    """Expose one or more Sling replications to Dagster as assets."""

    def __init__(
        self,
        dirpath: Path,
        resource: SlingResource,
        replication_specs: Sequence[SlingReplicationSpec],
        transforms: Sequence[Callable[[Definitions], Definitions]],
    ):
        self.dirpath = dirpath
        self.resource = resource
        self.replication_specs = replication_specs
        self.transforms = transforms

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
        return cls(
            dirpath=context.path,
            resource=params.sling or SlingResource(),
            replication_specs=context.resolve_context.resolve_value(params.replications),
            transforms=context.resolve_context.resolve_value(params.transforms),
        )

    def build_asset(
        self, context: ComponentLoadContext, replication_spec: SlingReplicationSpec
    ) -> AssetsDefinition:
        @sling_assets(
            name=replication_spec.op_spec.name or Path(replication_spec.relative_path).stem,
            op_tags=replication_spec.op_spec.tags,
            replication_config=self.dirpath / replication_spec.relative_path,
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
            assets=[
                self.build_asset(context, replication) for replication in self.replication_specs
            ],
        )
        for transform in self.transforms:
            defs = transform(defs)
        return defs
