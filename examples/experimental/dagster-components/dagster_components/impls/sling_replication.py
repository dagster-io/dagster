import os
from pathlib import Path
from typing import Optional

import yaml
from dagster._core.definitions.definitions_class import Definitions
from dagster_embedded_elt.sling import SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl


class OpSpecBaseModel(BaseModel):
    name: Optional[str] = None


class SlingReplicationParams(BaseModel):
    sling: SlingResource
    op: Optional[OpSpecBaseModel] = None


class SlingReplicationComponent(Component):
    params_schema = SlingReplicationParams

    def __init__(
        self, dirpath: Path, resource: SlingResource, op_spec: Optional[OpSpecBaseModel] = None
    ):
        self.dirpath = dirpath
        self.resource = resource
        self.op_spec = op_spec

    @classmethod
    def registered_name(cls) -> str:
        return "sling_replication"

    @classmethod
    def from_decl_node(cls, context: ComponentLoadContext, decl_node: ComponentDeclNode) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.defs_file_model.component_params
        )
        return cls(dirpath=decl_node.path, resource=loaded_params.sling, op_spec=loaded_params.op)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @sling_assets(
            name=self.op_spec.name if self.op_spec else self.dirpath.stem,
            replication_config=self.dirpath / "replication.yaml",
        )
        def _fn(context: AssetExecutionContext, sling: SlingResource):
            yield from sling.replicate(context=context)

        return Definitions(assets=[_fn], resources={"sling": self.resource})

    @classmethod
    def generate_files(cls) -> None:
        replication_path = Path(os.getcwd()) / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump(
                {"source": {}, "target": {}, "streams": {}},
                f,
            )
