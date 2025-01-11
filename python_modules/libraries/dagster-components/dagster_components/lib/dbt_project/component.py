from collections.abc import Iterator, Sequence
from typing import Annotated, Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component_type
from dagster_components.core.component_rendering import ResolvedFieldInfo
from dagster_components.core.dsl_schema import (
    AssetAttributesModel,
    AssetSpecTransform,
    OpSpecBaseModel,
)
from dagster_components.lib.dbt_project.generator import DbtProjectComponentGenerator
from dagster_components.utils import ResolvingInfo, get_wrapped_translator_class


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource
    op: Optional[OpSpecBaseModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvedFieldInfo(additional_scope={"node"})
    ] = None
    transforms: Optional[Sequence[AssetSpecTransform]] = None


@component_type(name="dbt_project")
class DbtProjectComponent(Component):
    def __init__(
        self,
        dbt_resource: DbtCliResource,
        op_spec: Optional[OpSpecBaseModel],
        asset_attributes: Optional[AssetAttributesModel],
        transforms: Sequence[AssetSpecTransform],
    ):
        self.dbt_resource = dbt_resource
        self.op_spec = op_spec
        self.transforms = transforms
        self.asset_attributes = asset_attributes

    @classmethod
    def get_generator(cls) -> "DbtProjectComponentGenerator":
        return DbtProjectComponentGenerator()

    @classmethod
    def get_component_schema_type(cls):
        return DbtProjectParams

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.get_component_schema_type())

        return cls(
            dbt_resource=loaded_params.dbt,
            op_spec=loaded_params.op,
            asset_attributes=loaded_params.asset_attributes,
            transforms=loaded_params.transforms or [],
        )

    def get_translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        project = DbtProject(self.dbt_resource.project_dir)
        project.prepare_if_dev()

        translator_cls = get_wrapped_translator_class(DagsterDbtTranslator)

        @dbt_assets(
            manifest=project.manifest_path,
            project=project,
            name=self.op_spec.name if self.op_spec else project.name,
            op_tags=self.op_spec.tags if self.op_spec else None,
            dagster_dbt_translator=translator_cls(
                base_translator=self.get_translator(),
                resolving_info=ResolvingInfo(
                    obj_name="node",
                    asset_attributes=self.asset_attributes or AssetAttributesModel(),
                    value_resolver=context.templated_value_resolver,
                ),
            ),
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.dbt_resource)

        defs = Definitions(assets=[_fn])
        for transform in self.transforms:
            defs = transform.apply(defs, context.templated_value_resolver)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
