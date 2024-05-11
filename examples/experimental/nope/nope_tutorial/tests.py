from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions


def hello_world_defs() -> Definitions:
    from hello_world import defs

    return defs


def custom_manifest_defs() -> Definitions:
    from custom_manifest import defs

    return defs


def single_file_manifest_def() -> Definitions:
    from single_file_manifest import defs

    return defs


def test_01_hello_world_execute_in_process() -> None:
    assert hello_world_defs().get_implicit_global_asset_job_def().execute_in_process().success


def test_02_custom_manifest_execute_in_process() -> None:
    assert custom_manifest_defs().get_implicit_global_asset_job_def().execute_in_process().success


def test_03_single_file_manifest_execute_in_process() -> None:
    defs = single_file_manifest_def()
    assert isinstance(defs, Definitions)
    key = AssetKey.from_user_string("group_a/asset_one")
    assert key.path == ["group_a", "asset_one"]
    assert isinstance(defs.get_assets_def(key), AssetsDefinition)
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
