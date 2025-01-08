from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.result import MaterializeResult
from dagster_embedded_elt.sling import DagsterSlingTranslator, SlingResource, sling_assets
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import TemplatedValueRenderer, component_type
from dagster_components.core.component_generator import ComponentGenerator
from dagster_components.core.dsl_schema import (
    AssetAttributes,
    AssetAttributesModel,
    AssetSpecProcessor,
    OpSpecBaseModel,
)


class SlingReplicationParams(BaseModel):
    path: str
    op: Optional[OpSpecBaseModel] = None
    translator: Optional[AssetAttributesModel] = None


class SlingReplicationCollectionParams(BaseModel):
    sling: Optional[SlingResource] = None
    replications: Sequence[SlingReplicationParams]
    asset_attributes: Optional[AssetAttributes] = None


class SlingReplicationTranslator(DagsterSlingTranslator):
    def __init__(
        self,
        *,
        params: Optional[AssetAttributesModel],
        value_renderer: TemplatedValueRenderer,
    ):
        self.params = params or AssetAttributesModel()
        self.value_renderer = value_renderer

    def _get_rendered_attribute(
        self, attribute: str, stream_definition: Mapping[str, Any], default_method
    ) -> Any:
        renderer = self.value_renderer.with_context(stream_definition=stream_definition)
        rendered_attribute = self.params.render_properties(renderer).get(attribute)
        return (
            rendered_attribute
            if rendered_attribute is not None
            else default_method(stream_definition)
        )

    def get_asset_key(self, stream_definition: Mapping[str, Any]) -> AssetKey:
        return self._get_rendered_attribute("key", stream_definition, super().get_asset_key)

    def get_group_name(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        return self._get_rendered_attribute("group_name", stream_definition, super().get_group_name)

    def get_tags(self, stream_definition: Mapping[str, Any]) -> Mapping[str, str]:
        return self._get_rendered_attribute("tags", stream_definition, super().get_tags)

    def get_metadata(self, stream_definition: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._get_rendered_attribute("metadata", stream_definition, super().get_metadata)

    def get_auto_materialize_policy(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[AutoMaterializePolicy]:
        return self._get_rendered_attribute(
            "auto_materialize_policy", stream_definition, super().get_auto_materialize_policy
        )


@component_type(name="sling_replication_collection")
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
    def get_generator(cls) -> ComponentGenerator:
        from dagster_components.lib.sling_replication_collection.generator import (
            SlingReplicationComponentGenerator,
        )

        return SlingReplicationComponentGenerator()

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
            name=replication.op.name if replication.op else Path(replication.path).stem,
            op_tags=replication.op.tags if replication.op else {},
            replication_config=self.dirpath / replication.path,
            dagster_sling_translator=SlingReplicationTranslator(
                params=replication.translator,
                value_renderer=context.templated_value_renderer,
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
            defs = transform.apply(defs, context.templated_value_renderer)
        return defs
