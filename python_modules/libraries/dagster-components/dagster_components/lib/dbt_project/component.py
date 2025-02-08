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

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.common.schema import AssetAttributesSchema, OpSpecSchema
from dagster_components.core.component import registered_component_type
from dagster_components.core.resolution_engine.context import ResolutionContext
from dagster_components.core.resolution_engine.resolver import Resolver, resolver
from dagster_components.core.schema.base import ComponentSchema
from dagster_components.core.schema.metadata import SchemaFieldInfo
from dagster_components.core.schema.objects import AssetSpecTransformSchema
from dagster_components.lib.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.utils import TranslatorResolvingInfo, get_wrapped_translator_class


class DbtProjectParams(ComponentSchema):
    dbt: DbtCliResource
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema], SchemaFieldInfo(required_scope={"node"})
    ] = None
    transforms: Optional[Sequence[AssetSpecTransformSchema]] = None


@resolver(fromtype=DbtProjectParams, exclude_fields={"asset_attributes"})
class DbtProjectResolver(Resolver[DbtProjectParams]):
    def resolve_translator(self, context: ResolutionContext) -> DagsterDbtTranslator:
        return get_wrapped_translator_class(DagsterDbtTranslator)(
            resolving_info=TranslatorResolvingInfo(
                "node", self.schema.asset_attributes or AssetAttributesSchema(), context
            )
        )


@registered_component_type(name="dbt_project")
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    def __init__(
        self,
        dbt: DbtCliResource,
        op: Optional[OpSpecSchema],
        translator: DagsterDbtTranslator,
        transforms: Optional[Sequence[Callable[[Definitions], Definitions]]] = None,
    ):
        self.resource = dbt
        self.project = DbtProject(dbt.project_dir)
        self.op_spec = op
        self.transforms = transforms or []
        self.translator = translator

    @classmethod
    def get_scaffolder(cls) -> "DbtProjectComponentScaffolder":
        return DbtProjectComponentScaffolder()

    @classmethod
    def get_schema(cls) -> type[DbtProjectParams]:
        return DbtProjectParams

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
            name=self.op_spec.name if self.op_spec else self.project.name,
            op_tags=self.op_spec.tags if self.op_spec else None,
            dagster_dbt_translator=self.translator,
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.resource)

        defs = Definitions(assets=[_fn])
        for transform in self.transforms:
            defs = transform(defs)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
