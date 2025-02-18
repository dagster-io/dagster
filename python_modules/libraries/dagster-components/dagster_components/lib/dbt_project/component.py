from collections.abc import Iterator, Sequence
from typing import Annotated, Callable, Optional

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
from dagster_components.core.component import registered_component_type
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetSpecTransformSchema,
    OpSpecSchema,
    ResolutionContext,
)
from dagster_components.lib.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


class DbtProjectSchema(ResolvableSchema["DbtProjectComponent"]):
    dbt: DbtCliResource
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema],
        ResolvableFieldInfo(required_scope={"node"}),
    ] = None
    transforms: Optional[Sequence[AssetSpecTransformSchema]] = None


def resolve_dbt(context: ResolutionContext, schema: DbtProjectSchema) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(schema.dbt.model_dump()))


def resolve_translator(
    context: ResolutionContext, schema: DbtProjectSchema
) -> DagsterDbtTranslator:
    return get_wrapped_translator_class(DagsterDbtTranslator)(
        resolving_info=TranslatorResolvingInfo(
            "node", schema.asset_attributes or AssetAttributesSchema(), context
        )
    )


@registered_component_type(name="dbt_project")
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))  # omits translator prop from schema
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, FieldResolver(resolve_dbt)]
    op: Optional[OpSpecSchema] = Field(
        None, description="Customizations to the op underlying the dbt run."
    )
    translator: Annotated[DagsterDbtTranslator, FieldResolver(resolve_translator)] = Field(
        default_factory=lambda: DagsterDbtTranslator()
    )
    transforms: Optional[Sequence[Callable[[Definitions], Definitions]]] = None

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
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.dbt)

        defs = Definitions(assets=[_fn])
        for transform in self.transforms or []:
            defs = transform(defs)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
