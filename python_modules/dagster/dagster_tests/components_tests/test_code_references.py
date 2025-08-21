import tempfile
from pathlib import Path

import dagster as dg
import pytest
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    CacheableAssetsDefinition,
)
from dagster._core.test_utils import new_cwd
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.defs_module import CompositeYamlComponent
from dagster_shared.yaml_utils.source_position import LineCol, SourcePosition


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return []

    def build_definitions(self, data):
        @dg.asset
        def my_asset():
            return 1

        return [my_asset]


@pytest.mark.skip("Find a way to set up this test with new Tree system")
class CustomComponent(dg.Component):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions(
            assets=[dg.AssetSpec(key="asset1"), MyCacheableAssetsDefinition(unique_id="my_asset")]
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
        spec = next(a for a in assets if isinstance(a, dg.AssetSpec))
        assert isinstance(spec, dg.AssetSpec)
        assert "dagster/code_references" in spec.metadata
        cacheable_asset = next(a for a in assets if isinstance(a, MyCacheableAssetsDefinition))
        assert isinstance(cacheable_asset, MyCacheableAssetsDefinition)
