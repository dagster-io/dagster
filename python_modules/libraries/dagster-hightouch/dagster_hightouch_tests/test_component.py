from unittest.mock import MagicMock
import dagster as dg
from dagster_hightouch import HightouchSyncComponent


def test_hightouch_component_load():
    asset_key_str = "test_hightouch_asset"
    component = HightouchSyncComponent(
        sync_id="123", asset=dg.AssetSpec(key=asset_key_str)
    )

    defs = dg.Definitions.merge(
        component.build_defs(MagicMock()),
        dg.Definitions(resources={"hightouch": dg.ResourceDefinition.mock_resource()}),
    )

    assets_def = defs.get_assets_def(asset_key_str)
    assert assets_def
    assert dg.AssetKey([asset_key_str]) in assets_def.keys


def test_component_definition():
    component = HightouchSyncComponent(
        sync_id="test_id", asset=dg.AssetSpec(key=["hightouch", "my_sync"])
    )

    defs = dg.Definitions.merge(
        component.build_defs(MagicMock()),
        dg.Definitions(resources={"hightouch": dg.ResourceDefinition.mock_resource()}),
    )

    assert isinstance(defs, dg.Definitions)
    assert len(list(defs.get_all_asset_specs())) == 1
