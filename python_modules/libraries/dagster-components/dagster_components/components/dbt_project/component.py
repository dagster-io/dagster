from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property
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

from dagster_components import Component, ComponentLoadContext, FieldResolver
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.core.schema.base import PlainSamwiseSchema
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


class DbtProjectSchema(PlainSamwiseSchema):
    dbt: DbtCliResource
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"node"}),
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorSchema]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None


@scaffoldable(scaffolder=DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[
        DbtCliResource,
        FieldResolver(
            lambda context, schema: DbtCliResource(**context.resolve_value(schema.dbt.model_dump()))
        ),
    ]
    op: Annotated[
        Optional[OpSpec],
        FieldResolver(lambda context, schema: OpSpec.from_optional_schema(context, schema.op)),
    ] = None

    @staticmethod
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

    translator: Annotated[DagsterDbtTranslator, FieldResolver(resolve_translator)] = field(
        default_factory=DagsterDbtTranslator
    )

    asset_post_processors: Annotated[
        Optional[Sequence[PostProcessorFn]],
        FieldResolver(
            lambda context, schema: [
                resolve_schema_to_post_processor(context, schema)
                for schema in schema.asset_post_processors or []
            ]
        ),
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
