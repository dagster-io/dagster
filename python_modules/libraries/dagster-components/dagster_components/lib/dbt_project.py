import os
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional

import click
import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils import pushd
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from dbt.cli.main import dbtRunner
from jinja2 import Template
from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import component
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl
from dagster_components.core.dsl_schema import OpSpecBaseModel


class DbtNodeTranslatorParams(BaseModel):
    key: Optional[str] = None
    group: Optional[str] = None


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource
    op: Optional[OpSpecBaseModel] = None
    translator: Optional[DbtNodeTranslatorParams] = None


class DbtGenerateParams(BaseModel):
    init: bool = Field(default=False)
    project_path: Optional[str] = None

    @staticmethod
    @click.command
    @click.option("--project-path", "-p", type=click.Path(resolve_path=True), default=None)
    @click.option("--init", "-i", is_flag=True, default=False)
    def cli(project_path: Optional[str], init: bool) -> "DbtGenerateParams":
        return DbtGenerateParams(project_path=project_path, init=init)


class DbtProjectComponentTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        *,
        translator_params: Optional[DbtNodeTranslatorParams] = None,
    ):
        self.translator_params = translator_params

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        if not self.translator_params or not self.translator_params.key:
            return super().get_asset_key(dbt_resource_props)

        return AssetKey.from_user_string(
            Template(self.translator_params.key).render(node=dbt_resource_props)
        )

    def get_group_name(self, dbt_resource_props) -> Optional[str]:
        if not self.translator_params or not self.translator_params.group:
            return super().get_group_name(dbt_resource_props)

        return Template(self.translator_params.group).render(node=dbt_resource_props)


@component(name="dbt_project")
class DbtProjectComponent(Component):
    params_schema = DbtProjectParams
    generate_params_schema = DbtGenerateParams

    def __init__(
        self,
        dbt_resource: DbtCliResource,
        op_spec: Optional[OpSpecBaseModel],
        dbt_translator: Optional[DagsterDbtTranslator],
    ):
        self.dbt_resource = dbt_resource
        self.op_spec = op_spec
        self.dbt_translator = dbt_translator

    @classmethod
    def from_decl_node(cls, context: ComponentLoadContext, decl_node: ComponentDeclNode) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)

        # all paths should be resolved relative to the directory we're in
        with pushd(str(decl_node.path)):
            loaded_params = TypeAdapter(cls.params_schema).validate_python(
                decl_node.component_file_model.params
            )
        return cls(
            dbt_resource=loaded_params.dbt,
            op_spec=loaded_params.op,
            dbt_translator=DbtProjectComponentTranslator(
                translator_params=loaded_params.translator
            ),
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

        return Definitions(assets=[_fn])

    @classmethod
    def generate_files(cls, params: DbtGenerateParams) -> Mapping[str, Any]:
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

        return {"dbt": {"project_dir": relative_path}}

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
