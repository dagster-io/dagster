from collections.abc import Iterator, Sequence
from typing import Annotated, Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtManifestAssetSelection,
    DbtProject,
    dbt_assets,
)
from pydantic import ConfigDict, Field, computed_field
from pydantic.dataclasses import dataclass

from dagster_components import Component, ComponentLoadContext, FieldResolver
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessorSchema,
    OpSpec,
    OpSpecSchema,
    PostProcessorFn,
    ResolutionContext,
)
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


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))  # omits translator prop from schema
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, FieldResolver(resolve_dbt)]
    op: Optional[OpSpec] = Field(
        None, description="Customizations to the op underlying the dbt run."
    )
    translator: Annotated[DagsterDbtTranslator, FieldResolver(resolve_translator)] = Field(
        default_factory=lambda: DagsterDbtTranslator()
    )
    asset_post_processors: Optional[Sequence[PostProcessorFn]] = None
    select: str = Field(
        default="fqn:*",
        description="A dbt selection string which specifies a subset of dbt nodes to represent as assets.",
    )
    exclude: Optional[str] = Field(
        default=None,
        description="A dbt selection string which specifies a subset of dbt nodes to exclude from the set of assets.",
    )

    @computed_field
    @property
    def project(self) -> DbtProject:
        return DbtProject(self.dbt.project_dir)

    @classmethod
    def get_scaffolder(cls) -> "DbtProjectComponentScaffolder":
        return DbtProjectComponentScaffolder()

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
