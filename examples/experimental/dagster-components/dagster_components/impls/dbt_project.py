import os
from pathlib import Path
from typing import Any, Mapping, Optional

import dagster._check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from dbt.cli.main import dbtRunner
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl


class DbtProjectParams(BaseModel):
    dbt: DbtCliResource


class DbtGenerateParams(BaseModel):
    init: bool = False
    project_path: Optional[str] = None


class DbtProjectComponent(Component):
    params_schema = DbtProjectParams
    generate_params_schema = DbtGenerateParams

    def __init__(self, dbt_resource: DbtCliResource):
        self.dbt_resource = dbt_resource

    @classmethod
    def registered_name(cls) -> str:
        return "dbt_project"

    @classmethod
    def from_decl_node(cls, context: ComponentLoadContext, decl_node: ComponentDeclNode) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)

        # all paths should be resolved relative to the directory we're in
        with pushd(str(decl_node.path)):
            loaded_params = TypeAdapter(cls.params_schema).validate_python(
                decl_node.defs_file_model.component_params
            )
        return cls(dbt_resource=loaded_params.dbt)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        project = DbtProject(self.dbt_resource.project_dir)
        project.prepare_if_dev()

        @dbt_assets(manifest=project.manifest_path, project=project)
        def _fn(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        return Definitions(assets=[_fn], resources={"dbt": self.dbt_resource})

    @classmethod
    def generate_files(cls, params: DbtGenerateParams) -> Mapping[str, Any]:
        if params.project_path:
            relative_path = os.path.relpath(params.project_path, start=os.getcwd())
        elif params.init:
            dbtRunner().invoke(["init"])
            subpaths = list(Path(os.getcwd()).iterdir())
            check.invariant(len(subpaths) == 1, "Expected exactly one subpath to be created.")
            # this path should be relative to this directory
            relative_path = subpaths[0].name
        else:
            relative_path = None

        return {"dbt": {"project_dir": relative_path}}
