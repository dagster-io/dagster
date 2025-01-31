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
from dagster_components.core.component import component_type
from dagster_components.core.component_scaffolder import ComponentScaffolder
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecModel,
)
from dagster_components.core.schema.resolution import ResolvableModel, TemplatedValueResolver
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


@record
class SlingReplicationSpec:
    relative_path: str
    op: OpSpecModel
    translator: DagsterSlingTranslator


def get_translator(attributes: Optional[AssetAttributesModel], resolver: TemplatedValueResolver):
    return get_wrapped_translator_class(DagsterSlingTranslator)(
        resolving_info=ResolvingInfo(
            "stream_definition", attributes or AssetAttributesModel(), resolver
        )
    )


class SlingReplicationParams(ResolvableModel[SlingReplicationSpec]):
    path: Annotated[str, ResolvableFieldInfo(resolved_name="relative_path")]
    op: OpSpecModel = OpSpecModel()
    asset_attributes: Annotated[
        Optional[AssetAttributesModel],
        ResolvableFieldInfo(
            required_scope={"stream_definition"},
            resolved_name="translator",
            pre_process_fn=lambda attributes, _: attributes,
            post_process_fn=get_translator,
        ),
    ] = None


class SlingReplicationCollectionParams(ResolvableModel):
    sling: Optional[SlingResource] = SlingResource()
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@component_type
class SlingReplicationCollection(Component):
    """Expose one or more Sling replications to Dagster as assets."""

    def __init__(
        self,
        resource: SlingResource,
        replication_specs: Sequence[SlingReplicationSpec],
        transforms: Sequence[Callable[[Definitions], Definitions]],
    ):
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
        return params.resolve_as(cls, context.templated_value_resolver)

    def build_asset(
        self, context: ComponentLoadContext, replication_spec: SlingReplicationSpec
    ) -> AssetsDefinition:
        @sling_assets(
            name=replication_spec.op.name or Path(replication_spec.relative_path).stem,
            op_tags=replication_spec.op.tags,
            replication_config=context.path / replication_spec.relative_path,
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
