from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_embedded_elt.sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel, Field
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import (
    ComponentGenerateRequest,
    TemplatedValueResolver,
    component,
)
from dagster_components.core.component_rendering import RenderingScope
from dagster_components.core.dsl_schema import AssetAttributes, AssetSpecProcessor, OpSpecBaseModel
from dagster_components.generate import generate_component_yaml


class SlingReplicationTranslatorParams(BaseModel):
    key: Optional[str] = None
    group_name: Optional[str] = None


class SlingReplicationParams(BaseModel):
    path: str
    op: Optional[OpSpecBaseModel] = None
    translator: Optional[SlingReplicationTranslatorParams] = RenderingScope(
        Field(None), required_scope={"stream_definition"}
    )


class SlingReplicationCollectionParams(BaseModel):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    asset_attributes: Optional[AssetAttributes] = None


class SlingReplicationTranslator(DagsterSlingTranslator):
    def __init__(
        self,
        *,
        value_resolver: TemplatedValueResolver,
        translator_params: Optional[SlingReplicationTranslatorParams] = None,
    ):
        self.value_resolver = value_resolver
        self.translator_params = translator_params

    def get_asset_key(self, stream_definition: Mapping[str, Any]) -> AssetKey:
        if not self.translator_params or not self.translator_params.key:
            return super().get_asset_key(stream_definition)

        return self.value_resolver.with_context(stream_definition=stream_definition).resolve(
            self.translator_params.key
        )

    def get_group_name(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        if not self.translator_params or not self.translator_params.group_name:
            return super().get_group_name(stream_definition)
        return self.value_resolver.with_context(stream_definition=stream_definition).resolve(
            self.translator_params.group_name
        )


@component(name="sling_replication_collection")
class SlingReplicationCollectionComponent(Component):
    params_schema = SlingReplicationCollectionParams

    def __init__(
        self,
        dirpath: Path,
        resource: SlingResource,
        sling_replications: Sequence[SlingReplicationParams],
        asset_attributes: Sequence[AssetSpecProcessor],
    ):
        self.dirpath = dirpath
        self.resource = resource
        self.sling_replications = sling_replications
        self.asset_attributes = asset_attributes

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        loaded_params = context.load_params(cls.params_schema)
        return cls(
            dirpath=context.path,
            resource=loaded_params.sling or SlingResource(),
            sling_replications=loaded_params.replications,
            asset_attributes=loaded_params.asset_attributes or [],
        )

    def build_replication_asset(
        self, context: ComponentLoadContext, replication: SlingReplicationParams
    ) -> AssetsDefinition:
        @sling_assets(
            name=replication.op.name if replication.op else self.dirpath.stem,
            op_tags=replication.op.tags if replication.op else {},
            replication_config=self.dirpath / replication.path,
            dagster_sling_translator=SlingReplicationTranslator(
                value_resolver=context.templated_value_resolver,
                translator_params=replication.translator,
            ),
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(context=context, sling=self.resource)

        return _asset

    def execute(
        self, context: AssetExecutionContext, sling: SlingResource
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        yield from sling.replicate(context=context)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs = Definitions(
            assets=[
                self.build_replication_asset(context, replication)
                for replication in self.sling_replications
            ],
        )
        for transform in self.asset_attributes:
            defs = transform.apply(defs)
        return defs

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        generate_component_yaml(request, params)
