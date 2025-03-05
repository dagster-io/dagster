from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_sling.resources import AssetExecutionContext
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass
from typing_extensions import TypeAlias

from dagster_components import Component, ComponentLoadContext, FieldResolver
from dagster_components.components.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessorSchema,
    OpSpec,
    OpSpecSchema,
    PostProcessorFn,
)
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.utils import TranslatorResolvingInfo


class ResolvingSlingTranslator(DagsterSlingTranslator):
    def __init__(self, *, resolving_info: TranslatorResolvingInfo):
        self.resolving_info = resolving_info

    def get_asset_spec(self, base_spec: AssetSpec) -> AssetSpec:
        return self.resolving_info.get_asset_spec(
            base_spec,
            {},
        )


def resolve_translator(
    context: ResolutionContext, schema: "SlingReplicationSchema"
) -> DagsterSlingTranslator:
    # TODO: Consider supporting owners and code_version in the future
    if schema.asset_attributes and schema.asset_attributes.owners:
        raise ValueError("owners are not supported for sling_replication_collection component")
    if schema.asset_attributes and schema.asset_attributes.code_version:
        raise ValueError("code_version is not supported for sling_replication_collection component")
    return ResolvingSlingTranslator(
        resolving_info=TranslatorResolvingInfo(
            "stream_definition",
            schema.asset_attributes or AssetAttributesSchema(),
            context,
        )
    )


SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


class SlingReplicationSpec(BaseModel):
    path: str
    op: Optional[OpSpec]
    translator: Annotated[Optional[DagsterSlingTranslator], FieldResolver(resolve_translator)]
    include_metadata: list[SlingMetadataAddons]


class SlingReplicationSchema(ResolvableSchema[SlingReplicationSpec]):
    path: str = Field(
        ...,
        description="The path to the Sling replication file. For more information, see https://docs.slingdata.io/concepts/replication#overview.",
    )
    op: Optional[OpSpecSchema] = Field(
        None,
        description="Customizations to the op underlying the Sling replication.",
    )
    include_metadata: list[SlingMetadataAddons] = Field(
        ["column_metadata", "row_count"],
        description="The metadata to include on materializations of the assets produced by the Sling replication.",
    )
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"stream_definition"}),
    ] = Field(
        None,
        description="Customizations to the assets produced by the Sling replication.",
    )


class SlingReplicationCollectionSchema(ResolvableSchema["SlingReplicationCollectionComponent"]):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationSchema]
    asset_post_processors: Optional[Sequence[AssetPostProcessorSchema]] = None


def resolve_resource(
    context: ResolutionContext, schema: SlingReplicationCollectionSchema
) -> SlingResource:
    return (
        SlingResource(**context.resolve_value(schema.sling.model_dump()))
        if schema.sling
        else SlingResource()
    )


@scaffoldable(scaffolder=SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component):
    """Expose one or more Sling replications to Dagster as assets."""

    resource: Annotated[SlingResource, FieldResolver(resolve_resource)] = Field(
        ..., description="Customizations to Sling execution."
    )
    replications: Sequence[SlingReplicationSpec] = Field(
        ..., description="A set of Sling replications to expose as assets."
    )
    asset_post_processors: Optional[Sequence[PostProcessorFn]] = Field(
        default=None,
        description="Post-processors to apply to the asset definitions produced by this component.",
    )

    @classmethod
    def get_schema(cls) -> type[SlingReplicationCollectionSchema]:
        return SlingReplicationCollectionSchema

    def build_asset(
        self, context: ComponentLoadContext, replication_spec: SlingReplicationSpec
    ) -> AssetsDefinition:
        op_spec = replication_spec.op or OpSpec()

        @sling_assets(
            name=op_spec.name or Path(replication_spec.path).stem,
            op_tags=op_spec.tags,
            replication_config=context.path / replication_spec.path,
            dagster_sling_translator=replication_spec.translator,
            backfill_policy=op_spec.backfill_policy,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(
                context=context, sling=self.resource, replication_spec=replication_spec
            )

        return _asset

    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec: SlingReplicationSpec,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        iterator = sling.replicate(context=context)
        if "column_metadata" in replication_spec.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in replication_spec.include_metadata:
            iterator = iterator.fetch_row_count()
        yield from iterator

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = Definitions(
            assets=[self.build_asset(context, replication) for replication in self.replications],
        )
        for post_processor in self.asset_post_processors or []:
            defs = post_processor(defs)
        return defs
