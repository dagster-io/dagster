from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from types import ModuleType
from typing import Annotated, Optional, cast

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtManifestAssetSelection,
    DbtProject,
    dbt_assets,
)
<<<<<<< HEAD
from dagster_dbt.asset_utils import get_asset_key_for_model as get_asset_key_for_model
=======
from dagster_dbt.asset_utils import (
    get_asset_key_for_model as base_get_asset_key_for_model,
    get_manifest_and_translator_from_dbt_assets,
)
from pydantic import ConfigDict, Field, computed_field
from pydantic.dataclasses import dataclass
>>>>>>> 4eb6644f8c ([dagster-components][dbt] Add utility to construct DbtManifestAssetSelection for a component)

from dagster_components import Component, ComponentLoadContext
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    AssetPostProcessorModel,
    OpSpec,
    OpSpecModel,
    ResolutionContext,
)
from dagster_components.resolved.metadata import ResolvableFieldInfo
from dagster_components.resolved.model import FieldResolver, ResolvableModel, ResolvedFrom
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


class DbtProjectModel(ResolvableModel):
    dbt: DbtCliResource
    op: Optional[OpSpecModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel],
        ResolvableFieldInfo(required_scope={"node"}),
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None


def resolve_translator(context: ResolutionContext, model: DbtProjectModel) -> DagsterDbtTranslator:
    if model.asset_attributes and model.asset_attributes.deps:
        # TODO: Consider supporting alerting deps in the future
        raise ValueError("deps are not supported for dbt_project component")
    return get_wrapped_translator_class(DagsterDbtTranslator)(
        resolving_info=TranslatorResolvingInfo(
            "node", model.asset_attributes or AssetAttributesModel(), context
        )
    )


def resolve_dbt(context: ResolutionContext, dbt: DbtCliResource) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(dbt.model_dump()))


@scaffoldable(scaffolder=DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component, ResolvedFrom[DbtProjectModel]):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, FieldResolver(resolve_dbt)]
    op: Annotated[Optional[OpSpec], FieldResolver(OpSpec.from_optional)] = None
    # This requires from_parent because it access asset_attributes in the model
    translator: Annotated[DagsterDbtTranslator, FieldResolver.from_model(resolve_translator)] = (
        field(default_factory=DagsterDbtTranslator)
    )
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]],
        FieldResolver(AssetPostProcessor.from_optional_seq),
    ] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None

    @cached_property
    def project(self) -> DbtProject:
        return DbtProject(self.dbt.project_dir)

    def get_asset_selection(
        self, select: str, exclude: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        return DbtManifestAssetSelection.build(
            manifest=self.project.manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        self.project.prepare_if_dev()

        @dbt_assets(
            manifest=self.project.manifest_path,
            project=self.project,
            name=self.op.name if self.op else self.project.name,
            op_tags=self.op.tags if self.op else None,
            dagster_dbt_translator=self.translator,
            select=self.select,
            exclude=self.exclude,
            backfill_policy=self.op.backfill_policy if self.op else None,
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.dbt)

        defs = Definitions(assets=[_fn])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor.fn(defs)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()


def get_asset_key_for_model_from_module(
    context: ComponentLoadContext, dbt_component_module: ModuleType, model_name: str
) -> AssetKey:
    """Component-based version of dagster_dbt.get_asset_key_for_model. Returns the corresponding Dagster
    asset key for a dbt model, seed, or snapshot, loaded from the passed component path.

    Args:
        dbt_component_module (ModuleType): The module that was used to load the dbt project.
        model_name (str): The name of the dbt model, seed, or snapshot.

    Returns:
        AssetKey: The corresponding Dagster asset key.

    Examples:
        .. code-block:: python

            from dagster import asset
            from dagster_components.components.dbt_project import get_asset_key_for_model_from_module
            from dagster_components.core.component import ComponentLoadContext
            from my_project.defs import dbt_component

            ctx = ComponentLoadContext.get()

            @asset(deps={get_asset_key_for_model_from_module(ctx, dbt_component, "customers")})
            def cleaned_customers():
                ...
    """
    defs = context.load_defs(dbt_component_module)
    return get_asset_key_for_model(cast(Sequence[AssetsDefinition], defs.assets), model_name)


def asset_selection_for_component(
    context: ComponentLoadContext,
    dbt_component_module: ModuleType,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
) -> DbtManifestAssetSelection:
    """Constructs a DbtManifestAssetSelection, based on the dbt manifest and asset key mapping
    of the assets defined in the specified dagster_components.dagster_dbt.DbtAssetsComponent instance.

    Args:
        context (ComponentLoadContext): The context in which to load the component.
        dbt_component_module (ModuleType): The module that was used to load the dbt project.
        select (str): The dbt selection string to use when constructing the asset selection.
        exclude (Optional[str]): The dbt selection string to use when excluding assets from the asset selection.
    """
    defs = context.build_defs_from_component_module(dbt_component_module)
    manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(
        cast(Sequence[AssetsDefinition], defs.assets)
    )
    return DbtManifestAssetSelection.build(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude,
    )
