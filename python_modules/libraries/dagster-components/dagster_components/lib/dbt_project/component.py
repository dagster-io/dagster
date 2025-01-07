from typing import Any, Iterator, Mapping, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import TemplatedValueResolver, component_type
from dagster_components.core.dsl_schema import (
    AssetAttributes,
    AssetAttributesModel,
    AssetSpecProcessor,
    OpSpecBaseModel,
)
from dagster_components.lib.dbt_project.generator import DbtProjectComponentGenerator


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource
    op: Optional[OpSpecBaseModel] = None
    translator: Optional[AssetAttributesModel] = None
    asset_attributes: Optional[AssetAttributes] = None


class DbtProjectComponentTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        *,
        params: Optional[AssetAttributesModel],
        value_resolver: TemplatedValueResolver,
    ):
        self.params = params or AssetAttributesModel()
        self.value_resolver = value_resolver

    def _get_rendered_attribute(
        self, attribute: str, dbt_resource_props: Mapping[str, Any], default_method
    ) -> Any:
        resolver = self.value_resolver.with_context(node=dbt_resource_props)
        rendered_attribute = self.params.render_properties(resolver).get(attribute)
        return (
            rendered_attribute
            if rendered_attribute is not None
            else default_method(dbt_resource_props)
        )

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return self._get_rendered_attribute("key", dbt_resource_props, super().get_asset_key)

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        return self._get_rendered_attribute(
            "group_name", dbt_resource_props, super().get_group_name
        )

    def get_tags(self, dbt_resource_props):
        return self._get_rendered_attribute("tags", dbt_resource_props, super().get_tags)

    def get_automation_condition(self, dbt_resource_props):
        return self._get_rendered_attribute(
            "automation_condition", dbt_resource_props, super().get_automation_condition
        )


@component_type(name="dbt_project")
class DbtProjectComponent(Component):
    params_schema = DbtProjectParams

    def __init__(
        self,
        dbt_resource: DbtCliResource,
        op_spec: Optional[OpSpecBaseModel],
        dbt_translator: Optional[DagsterDbtTranslator],
        asset_processors: Sequence[AssetSpecProcessor],
    ):
        self.dbt_resource = dbt_resource
        self.op_spec = op_spec
        self.dbt_translator = dbt_translator
        self.asset_processors = asset_processors

    @classmethod
    def get_generator(cls) -> "DbtProjectComponentGenerator":
        return DbtProjectComponentGenerator()

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.params_schema)

        return cls(
            dbt_resource=loaded_params.dbt,
            op_spec=loaded_params.op,
            dbt_translator=DbtProjectComponentTranslator(
                params=loaded_params.translator,
                value_resolver=context.templated_value_resolver,
            ),
            asset_processors=loaded_params.asset_attributes or [],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        project = DbtProject(self.dbt_resource.project_dir)
        project.prepare_if_dev()

        @dbt_assets(
            manifest=project.manifest_path,
            project=project,
            name=self.op_spec.name if self.op_spec else project.name,
            op_tags=self.op_spec.tags if self.op_spec else None,
            dagster_dbt_translator=self.dbt_translator,
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.dbt_resource)

        defs = Definitions(assets=[_fn])
        for transform in self.asset_processors:
            defs = transform.apply(defs, context.templated_value_resolver)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
