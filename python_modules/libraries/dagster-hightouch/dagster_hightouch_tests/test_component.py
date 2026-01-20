from unittest.mock import MagicMock, patch
import dagster as dg
from dagster_hightouch import HightouchSyncComponent, ConfigurableHightouchResource
from dagster_hightouch.types import HightouchOutput
from typing import cast, Sequence


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


def test_component_execution():
    mock_output = HightouchOutput(
        sync_details={
            "destinationId": "dest1",
            "configuration": {"object": "test_obj"},
        },
        sync_run_details={
            "status": "success",
            "failedRows": {"addedCount": 5, "changedCount": 2, "removedCount": 1},
            "querySize": 100,
            "completionRatio": 1.0,
        },
        destination_details={"type": "salesforce", "slug": "sf-slug"},
    )

    resource_instance = ConfigurableHightouchResource(api_key="test-key")

    component = HightouchSyncComponent(
        sync_id="123", asset=dg.AssetSpec(key="test_asset")
    )
    defs = component.build_defs(MagicMock())

    with patch.object(
        ConfigurableHightouchResource, "sync_and_poll", return_value=mock_output
    ) as mock_method:
        result = dg.materialize(
            assets=cast(Sequence[dg.AssetsDefinition], list(defs.assets or [])),
            resources={"hightouch": resource_instance},
        )

        assert result.success

        node_name = "hightouch_sync_test_asset"
        materializations = result.asset_materializations_for_node(node_name)

        metadata = materializations[0].metadata

        assert metadata["total_failed_rows"].value == 8
        assert metadata["failed_adds"].value == 5

        mock_method.assert_called_once_with("123")
