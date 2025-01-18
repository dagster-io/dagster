from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Annotated, Optional, Union

from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_sling.resources import AssetExecutionContext
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component_type
from dagster_components.core.component_scaffolder import ComponentScaffolder
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecBaseModel,
)
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


class SlingReplicationParams(BaseModel):
    path: str
    op: Optional[OpSpecBaseModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvableFieldInfo(additional_scope={"stream_definition"})
    ] = None


class SlingReplicationCollectionParams(BaseModel):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@component_type(name="sling_replication_collection")
class SlingReplicationCollectionComponent(Component):
    def __init__(
        self,
        dirpath: Path,
        resource: SlingResource,
        sling_replications: Sequence[SlingReplicationParams],
        transforms: Sequence[AssetSpecTransformModel],
    ):
        self.dirpath = dirpath
        self.resource = resource
        self.sling_replications = sling_replications
        self.transforms = transforms

    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        from dagster_components.lib.sling_replication_collection.scaffolder import (
            SlingReplicationComponentScaffolder,
        )

        return SlingReplicationComponentScaffolder()

    @classmethod
    def get_schema(cls):
        return SlingReplicationCollectionParams

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.get_schema())
        return cls(
            dirpath=context.path,
            resource=loaded_params.sling or SlingResource(),
            sling_replications=loaded_params.replications,
            transforms=loaded_params.transforms or [],
        )

    def build_replication_asset(
        self, context: ComponentLoadContext, replication: SlingReplicationParams
    ) -> AssetsDefinition:
        translator_cls = get_wrapped_translator_class(DagsterSlingTranslator)

        @sling_assets(
            name=replication.op.name if replication.op else Path(replication.path).stem,
            op_tags=replication.op.tags if replication.op else {},
            replication_config=self.dirpath / replication.path,
            dagster_sling_translator=translator_cls(
                base_translator=DagsterSlingTranslator(),
                resolving_info=ResolvingInfo(
                    obj_name="stream_definition",
                    asset_attributes=replication.asset_attributes or AssetAttributesModel(),
                    value_resolver=context.templated_value_resolver,
                ),
            ),
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
                self.build_replication_asset(context, replication)
                for replication in self.sling_replications
            ],
        )
        for transform in self.transforms:
            defs = transform.apply(defs, context.templated_value_resolver)
        return defs
