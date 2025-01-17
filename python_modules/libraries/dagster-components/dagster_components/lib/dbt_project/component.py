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
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component_type
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesModel,
    AssetSpecTransformModel,
    OpSpecBaseModel,
    TemplatedValueResolver,
)
from dagster_components.lib.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource
    op: Optional[OpSpecBaseModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvableFieldInfo(additional_scope={"node"})
    ] = None
    transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@component_type(name="dbt_project")
class DbtProjectComponent(Component):
    def __init__(
        self,
        dbt_resource: DbtCliResource,
        op_spec: Optional[OpSpecBaseModel],
        asset_attributes: Optional[AssetAttributesModel],
        transforms: Sequence[AssetSpecTransformModel],
        value_resolver: TemplatedValueResolver,
    ):
        self.dbt_resource = dbt_resource
        self.project = DbtProject(self.dbt_resource.project_dir)
        self.op_spec = op_spec
        self.asset_attributes = asset_attributes
        self.transforms = transforms
        self.value_resolver = value_resolver
        self.translator = self._get_wrapped_translator()

    @classmethod
    def get_scaffolder(cls) -> "DbtProjectComponentScaffolder":
        return DbtProjectComponentScaffolder()

    @classmethod
    def get_schema(cls):
        return DbtProjectParams

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.get_schema())

        return cls(
            dbt_resource=loaded_params.dbt,
            op_spec=loaded_params.op,
            asset_attributes=loaded_params.asset_attributes,
            transforms=loaded_params.transforms or [],
            value_resolver=context.templated_value_resolver,
        )

    def get_translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator()

    def _get_wrapped_translator(self) -> DagsterDbtTranslator:
        translator_cls = get_wrapped_translator_class(DagsterDbtTranslator)
        return translator_cls(
            base_translator=self.get_translator(),
            resolving_info=ResolvingInfo(
                obj_name="node",
                asset_attributes=self.asset_attributes or AssetAttributesModel(),
                value_resolver=self.value_resolver,
            ),
        )

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
            yield from self.execute(context=context, dbt=self.dbt_resource)

        defs = Definitions(assets=[_fn])
        for transform in self.transforms:
            defs = transform.apply(defs, context.templated_value_resolver)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
