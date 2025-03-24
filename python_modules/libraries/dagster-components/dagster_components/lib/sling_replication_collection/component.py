from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_sling.resources import AssetExecutionContext
from pydantic import Field
from typing_extensions import TypeAlias

from dagster_components.component.component import Component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.lib.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_components.resolved.context import ResolutionContext
from dagster_components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    AssetPostProcessorModel,
    OpSpec,
    OpSpecModel,
)
from dagster_components.resolved.metadata import ResolvableFieldInfo
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver
from dagster_components.scaffold.scaffold import scaffold_with
from dagster_components.utils import TranslatorResolvingInfo

SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


class DagsterSlingTranslatorAutomationCondition(DagsterSlingTranslator):
    """Subclassed to pull in any overridden impl for get_automation_condition
    into produced asset specs.
    """

    def get_automation_condition(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[AutomationCondition]: ...

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        asset_spec = super().get_asset_spec(stream_definition)
        return asset_spec.replace_attributes(
            automation_condition=self.get_automation_condition(stream_definition)
        )


class ComponentsDagsterSlingTranslator(DagsterSlingTranslator):
    def __init__(self, *, resolving_info: TranslatorResolvingInfo):
        super().__init__()
        self.resolving_info = resolving_info

    def get_asset_spec(self, obj: Any) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        base_spec = super().get_asset_spec(obj)
        return self.resolving_info.get_asset_spec(
            base_spec,
            {self.resolving_info.obj_name: obj, "spec": base_spec},
        )


def resolve_translator(
    context: ResolutionContext, model: "SlingReplicationModel"
) -> DagsterSlingTranslator:
    # TODO: Consider supporting owners and code_version in the future
    if model.asset_attributes and isinstance(model.asset_attributes, AssetAttributesModel):
        if model.asset_attributes.owners:
            raise ValueError("owners are not supported for sling_replication_collection component")
        if model.asset_attributes.code_version:
            raise ValueError(
                "code_version is not supported for sling_replication_collection component"
            )

    return ComponentsDagsterSlingTranslator(
        resolving_info=TranslatorResolvingInfo(
            "stream_definition",
            model.asset_attributes or AssetAttributesModel(),
            context,
        )
    )


@dataclass
class SlingReplicationSpecModel(ResolvedFrom["SlingReplicationModel"]):
    path: str
    op: Annotated[Optional[OpSpec], Resolver.from_annotation()]
    translator: Annotated[Optional[DagsterSlingTranslator], Resolver.from_model(resolve_translator)]
    include_metadata: list[SlingMetadataAddons]


class SlingReplicationModel(ResolvableModel):
    path: str = Field(
        ...,
        description="The path to the Sling replication file. For more information, see https://docs.slingdata.io/concepts/replication#overview.",
    )
    op: Optional[OpSpecModel] = Field(
        None,
        description="Customizations to the op underlying the Sling replication.",
    )
    include_metadata: list[SlingMetadataAddons] = Field(
        ["column_metadata", "row_count"],
        description="The metadata to include on materializations of the assets produced by the Sling replication.",
    )
    asset_attributes: Annotated[
        Optional[Union[str, AssetAttributesModel]],
        ResolvableFieldInfo(required_scope={"stream_definition"}),
    ] = Field(
        None,
        description="Customizations to the assets produced by the Sling replication.",
    )


class SlingReplicationCollectionModel(ResolvableModel):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationModel]
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = None


def resolve_resource(
    context: ResolutionContext, model: SlingReplicationCollectionModel
) -> SlingResource:
    return (
        SlingResource(**context.resolve_value(model.sling.model_dump()))
        if model.sling
        else SlingResource()
    )


@scaffold_with(SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component, ResolvedFrom[SlingReplicationCollectionModel]):
    """Expose one or more Sling replications to Dagster as assets.

    [Sling](https://slingdata.io/) is a Powerful Data Integration tool enabling seamless ELT
    operations as well as quality checks across files, databases, and storage systems.

    dg scaffold dagster_components.dagster_sling.SlingReplicationCollectionComponent {component_name} to get started.

    This will create a component.yaml as well as a `replication.yaml` which is a Sling-specific configuration
    file. See Sling's [documentation](https://docs.slingdata.io/concepts/replication#overview) on `replication.yaml`.
    """

    resource: Annotated[SlingResource, Resolver.from_model(resolve_resource)] = ...
    replications: Annotated[Sequence[SlingReplicationSpecModel], Resolver.from_annotation()] = ...
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]], Resolver.from_annotation()
    ] = None

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
            defs = post_processor.fn(defs)
        return defs
