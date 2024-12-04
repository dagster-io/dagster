import os
from pathlib import Path

import yaml
from dagster._core.definitions.definitions_class import Definitions
from dagster_embedded_elt.sling import SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl


class SlingReplicationComponent(Component):
    params_schema = SlingResource

    def __init__(self, dirpath: Path, resource: SlingResource):
        self.dirpath = dirpath
        self.resource = resource

    @classmethod
    def registered_name(cls) -> str:
        return "sling_replication"

    @classmethod
    def from_decl_node(cls, context: ComponentLoadContext, decl_node: ComponentDeclNode) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.defs_file_model.component_params
        )
        return cls(dirpath=decl_node.path, resource=loaded_params)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @sling_assets(replication_config=self.dirpath / "replication.yaml")
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
