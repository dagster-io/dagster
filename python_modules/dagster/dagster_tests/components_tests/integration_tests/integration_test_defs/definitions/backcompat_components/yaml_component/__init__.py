from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster.components import Component, ComponentLoadContext


class MyYamlComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(
            assets=[AssetSpec(key=AssetKey(["foo"]))],
        )
