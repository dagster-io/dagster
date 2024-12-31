import os
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from dbt.cli.main import dbtRunner
from pydantic import BaseModel, Field
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import (
    ComponentGenerateRequest,
    TemplatedValueRenderer,
    component_type,
)
from dagster_components.core.dsl_schema import (
    AssetAttributes,
    AssetAttributesModel,
    AssetSpecProcessor,
    OpSpecBaseModel,
)
from dagster_components.generate import generate_component_yaml


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource
    op: Optional[OpSpecBaseModel] = None
    translator: Optional[AssetAttributesModel] = None
    asset_attributes: Optional[AssetAttributes] = None


class DbtGenerateParams(BaseModel):
    init: bool = Field(default=False)
    project_path: Optional[str] = None


class DbtProjectComponentTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        *,
        params: Optional[AssetAttributesModel],
        value_renderer: TemplatedValueRenderer,
    ):
        self.params = params or AssetAttributesModel()
        self.value_renderer = value_renderer

    def _get_rendered_attribute(
        self, attribute: str, dbt_resource_props: Mapping[str, Any], default_method
    ) -> Any:
        renderer = self.value_renderer.with_context(node=dbt_resource_props)
        rendered_attribute = self.params.render_properties(renderer).get(attribute)
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
    generate_params_schema = DbtGenerateParams

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
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.params_schema)

        return cls(
            dbt_resource=loaded_params.dbt,
            op_spec=loaded_params.op,
            dbt_translator=DbtProjectComponentTranslator(
                params=loaded_params.translator,
                value_renderer=context.templated_value_renderer,
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
            defs = transform.apply(defs, context.templated_value_renderer)
        return defs

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: DbtGenerateParams) -> None:
        cwd = os.getcwd()
        if params.project_path:
            # NOTE: CWD is not set "correctly" above so we prepend "../../.." as a temporary hack to
            # make sure the path is right.
            relative_path = os.path.join(
                "../../../", os.path.relpath(params.project_path, start=cwd)
            )
        elif params.init:
            dbtRunner().invoke(["init"])
            subpaths = [
                path for path in Path(cwd).iterdir() if path.is_dir() and path.name != "logs"
            ]
            check.invariant(len(subpaths) == 1, "Expected exactly one subpath to be created.")
            # this path should be relative to this directory
            relative_path = subpaths[0].name
        else:
            relative_path = None

        generate_component_yaml(request, {"dbt": {"project_dir": relative_path}})

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
