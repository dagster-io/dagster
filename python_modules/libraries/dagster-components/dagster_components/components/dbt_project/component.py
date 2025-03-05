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

from dagster_components import Component, ComponentLoadContext
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessor,
    AssetPostProcessorSchema,
    OpSpec,
    OpSpecSchema,
    ResolutionContext,
)
from dagster_components.core.schema.resolvable_from_schema import (
    ResolvableFromSchema,
    YamlFieldResolver,
    YamlSchema,
)
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


class DbtProjectSchema(YamlSchema):
    dbt: DbtCliResource
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"node"}),
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorSchema]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None


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


def resolve_dbt(context: ResolutionContext, dbt: DbtCliResource) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(dbt.model_dump()))


@scaffoldable(scaffolder=DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component, ResolvableFromSchema[DbtProjectSchema]):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, YamlFieldResolver(resolve_dbt)]
    op: Annotated[Optional[OpSpec], YamlFieldResolver(OpSpec.from_optional)] = None

    # This requires from_parent because it access asset_attributes in the schema
    translator: Annotated[
        DagsterDbtTranslator, YamlFieldResolver.from_parent(resolve_translator)
    ] = field(default_factory=DagsterDbtTranslator)
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]],
        YamlFieldResolver(AssetPostProcessor.from_optional_seq),
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
