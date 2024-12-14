import os
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Union

import yaml
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_embedded_elt.sling import SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import ComponentGenerateRequest, component
from dagster_components.core.component_decl_builder import ComponentDeclNode, YamlComponentDecl
from dagster_components.core.dsl_schema import AssetSpecProcessorModel, OpSpecBaseModel
from dagster_components.generate import generate_component_yaml


class SlingReplicationParams(BaseModel):
    sling: Optional[SlingResource] = None
    op: Optional[OpSpecBaseModel] = None
    asset_attributes: Optional[Sequence[AssetSpecProcessorModel]] = None


@component(name="sling_replication")
class SlingReplicationComponent(Component):
    params_schema = SlingReplicationParams

    def __init__(
        self,
        dirpath: Path,
        resource: SlingResource,
        op_spec: Optional[OpSpecBaseModel],
        asset_transforms: Sequence[AssetSpecProcessorModel],
    ):
        self.dirpath = dirpath
        self.resource = resource
        self.op_spec = op_spec
        self.asset_transforms = asset_transforms

    @classmethod
    def from_decl_node(cls, context: ComponentLoadContext, decl_node: ComponentDeclNode) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.component_file_model.params
        )
        return cls(
            dirpath=decl_node.path,
            resource=loaded_params.sling or SlingResource(),
            op_spec=loaded_params.op,
            asset_transforms=loaded_params.asset_attributes or [],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @sling_assets(
            name=self.op_spec.name if self.op_spec else self.dirpath.stem,
            op_tags=self.op_spec.tags if self.op_spec else {},
            replication_config=self.dirpath / "replication.yaml",
        )
        def _fn(context: AssetExecutionContext, sling: SlingResource):
            yield from self.execute(context=context, sling=sling)

        defs = Definitions(assets=[_fn], resources={"sling": self.resource})
        for transform in self.asset_transforms:
            defs = transform.transform(defs)
        return defs

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        generate_component_yaml(request, params)
        replication_path = Path(os.getcwd()) / "replication.yaml"
        with open(replication_path, "w") as f:
            yaml.dump(
                {"source": {}, "target": {}, "streams": {}},
                f,
            )

    def execute(
        self, context: AssetExecutionContext, sling: SlingResource
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        yield from sling.replicate(context=context)
