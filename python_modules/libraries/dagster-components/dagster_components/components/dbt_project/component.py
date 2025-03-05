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
from dagster_dbt.asset_utils import get_asset_key_for_model as get_asset_key_for_model

from dagster_components import Component, ComponentLoadContext, FieldResolver
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.core.schema.base import ResolvableSchema, resolve_as
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessorSchema,
    OpSpec,
    OpSpecSchema,
    PostProcessorFn,
    ResolutionContext,
    resolve_schema_to_post_processor,
)
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


class DbtProjectSchema(ResolvableSchema["DbtProjectComponent"]):
    dbt: DbtCliResource
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"node"}),
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorSchema]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None


def resolve_dbt(context: ResolutionContext, schema: DbtProjectSchema) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(schema.dbt.model_dump()))


def resolve_translator(
    context: ResolutionContext, schema: DbtProjectSchema
) -> DagsterDbtTranslator:
    if schema.asset_attributes and schema.asset_attributes.deps:
        # TODO: Consider supporting alerting deps in the future
        raise ValueError("deps are not supported for dbt_project component")
    return get_wrapped_translator_class(DagsterDbtTranslator)(
        resolving_info=TranslatorResolvingInfo(
            "node", schema.asset_attributes or AssetAttributesSchema(), context
        )
    )


def resolve_schema_to_post_processors(
    context: ResolutionContext, schema: DbtProjectSchema
) -> Sequence[PostProcessorFn]:
    return [
        resolve_schema_to_post_processor(context, s) for s in schema.asset_post_processors or []
    ]


def resolve_op_spec(context: ResolutionContext, schema: DbtProjectSchema) -> Optional[OpSpec]:
    return resolve_as(schema.op, target_type=OpSpec, context=context) if schema.op else None


@scaffoldable(scaffolder=DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, FieldResolver(resolve_dbt)]
    op: Annotated[Optional[OpSpec], FieldResolver(resolve_op_spec)] = None
    translator: Annotated[DagsterDbtTranslator, FieldResolver(resolve_translator)] = field(
        default_factory=DagsterDbtTranslator
    )
    asset_post_processors: Annotated[
        Optional[Sequence[PostProcessorFn]], FieldResolver(resolve_schema_to_post_processors)
    ] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None

    @cached_property
    def project(self) -> DbtProject:
        return DbtProject(self.dbt.project_dir)

    @classmethod
    def get_schema(cls) -> type[DbtProjectSchema]:
        return DbtProjectSchema

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
            defs = post_processor(defs)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()


def get_component_asset_key_for_model(
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
            from dagster_components.components.dbt_project import get_asset_key_for_model
            from dagster_components.core.component import ComponentLoadContext
            from my_project.defs import dbt_component

            ctx = ComponentLoadContext.get()

            @asset(deps={get_asset_key_for_model(ctx, dbt_component, "customers")})
            def cleaned_customers():
                ...
    """
    defs = context.build_defs_from_component_module(dbt_component_module)
    return get_asset_key_for_model(cast(Sequence[AssetsDefinition], defs.assets), model_name)
