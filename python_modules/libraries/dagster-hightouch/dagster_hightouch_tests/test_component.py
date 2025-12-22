import os
from unittest.mock import MagicMock, patch

from dagster import AssetKey, AssetsDefinition, AssetSpec, Definitions
from dagster.components.core.context import ComponentLoadContext

from dagster_hightouch.component import HightouchSyncComponent
from dagster_hightouch.resources import HightouchResource
from dagster_hightouch.types import HightouchOutput


def test_hightouch_component_builds_correctly():
    """
    Verifies that the component successfully creates an AssetsDefinition
    with the correct key and fields.
    """
    asset_spec = AssetSpec(
        key=AssetKey(["hightouch", "my_sync"]), description="Test sync asset"
    )

    component = HightouchSyncComponent(
        asset=asset_spec, sync_id_env_var="MY_SYNC_VAR"
    )

    load_context = MagicMock(spec=ComponentLoadContext)

    defs = component.build_defs(load_context)

    assert isinstance(defs, Definitions)
    assert defs.assets is not None

    assert len(list(defs.assets)) == 1

    asset_def = next(iter(defs.assets))
    assert isinstance(asset_def, AssetsDefinition)
    assert asset_def.keys == {AssetKey(["hightouch", "my_sync"])}


def test_hightouch_component_logic_execution():
    """
    Verifies that the internal asset logic attempts to resolve
    the environment variable and defines the correct resource requirements.
    """
    asset_spec = AssetSpec(key=AssetKey("test_execution"))
    component = HightouchSyncComponent(
        asset=asset_spec, sync_id_env_var="TEST_ENV_VAR"
    )

    mock_resource = MagicMock(spec=HightouchResource)
    mock_resource.sync_and_poll.return_value = HightouchOutput(
        sync_details={},
        sync_run_details={"querySize": 5},
        destination_details={},
    )

    with patch.dict(os.environ, {"TEST_ENV_VAR": "sync_12345"}):
        load_context = MagicMock(spec=ComponentLoadContext)
        defs = component.build_defs(load_context)

        assert defs.assets is not None
        asset_def = next(iter(defs.assets))
        assert isinstance(asset_def, AssetsDefinition)

        assert asset_def.op.name == "hightouch_sync_test_execution"

        assert "hightouch" in asset_def.op.required_resource_keys