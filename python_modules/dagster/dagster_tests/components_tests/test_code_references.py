import tempfile
from pathlib import Path

import pytest
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import new_cwd
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent
from dagster.components.core.tree import ComponentTree
from dagster_shared.yaml_utils.source_position import LineCol, SourcePosition


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return []

    def build_definitions(self, data):
        @asset
        def my_asset():
            return 1

        return [my_asset]


class CustomComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(
            assets=[AssetSpec(key="asset1"), MyCacheableAssetsDefinition(unique_id="my_asset")]
        )


@pytest.mark.skip("Find a way to set up this test with new Tree system")
def test_composite_yaml_component_code_references():
    with tempfile.TemporaryDirectory() as tmpdir, new_cwd(tmpdir):
        (Path(tmpdir) / "defs.yaml").touch()

        component = CompositeYamlComponent(
            components=[CustomComponent()],
            source_positions=[
                SourcePosition(
                    filename="test.py", start=LineCol(line=1, col=1), end=LineCol(line=1, col=1)
                )
            ],
            asset_post_processor_lists=[[]],
        )

        defs = component.build_defs(ComponentTree.for_test().load_context)
        assets = list(defs.assets or [])
        assert len(assets) == 2
        spec = next(a for a in assets if isinstance(a, AssetSpec))
        assert isinstance(spec, AssetSpec)
        assert "dagster/code_references" in spec.metadata
        cacheable_asset = next(a for a in assets if isinstance(a, MyCacheableAssetsDefinition))
        assert isinstance(cacheable_asset, MyCacheableAssetsDefinition)
