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
from dagster_components.core.component import registered_component_type
from dagster_components.core.schema.base import ResolvableModel
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecModel,
    TemplatedValueResolver,
)
from dagster_components.lib.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


class DbtProjectParams(ResolvableModel["DbtProjectComponent"]):
    dbt: DbtCliResource
    op: Optional[OpSpecModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvableFieldInfo(required_scope={"node"})
    ] = None
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None

    def resolve(self, resolver: TemplatedValueResolver) -> "DbtProjectComponent":
        return DbtProjectComponent(
            resource=self.dbt,
            op_spec=self.op.resolve(resolver) if self.op else None,
            translator=get_wrapped_translator_class(DagsterDbtTranslator)(
                resolving_info=ResolvingInfo(
                    "node", self.asset_attributes or AssetAttributesModel(), resolver
                )
            ),
            transforms=[transform.resolve(resolver) for transform in (self.transforms or [])],
        )


@registered_component_type(name="dbt_project")
class DbtProjectComponent(Component):
    """Expose a DBT project to Dagster as a set of assets."""

    def __init__(
        self,
        resource: DbtCliResource,
        op_spec: Optional[OpSpecModel],
        translator: DagsterDbtTranslator,
        transforms: Sequence[Callable[[Definitions], Definitions]],
    ):
        self.resource = resource
        self.project = DbtProject(resource.project_dir)
        self.op_spec = op_spec
        self.transforms = transforms
        self.translator = translator

    @classmethod
    def get_scaffolder(cls) -> "DbtProjectComponentScaffolder":
        return DbtProjectComponentScaffolder()

    @classmethod
    def get_schema(cls) -> type[DbtProjectParams]:
        return DbtProjectParams

    @classmethod
    def load(cls, params: DbtProjectParams, context: ComponentLoadContext) -> "DbtProjectComponent":
        return params.resolve(context.templated_value_resolver)

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
