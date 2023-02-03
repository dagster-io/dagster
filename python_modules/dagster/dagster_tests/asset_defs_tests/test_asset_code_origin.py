import os

from dagster import AssetsDefinition, load_assets_from_modules
from dagster._core.definitions.decorators.op_decorator import CODE_ORIGIN_TAG_NAME
from dagster._utils import file_relative_path


def test_asset_code_origins():
    from dagster_tests.asset_defs_tests import asset_package

    from .asset_package import module_with_assets

    collection_1 = load_assets_from_modules([asset_package, module_with_assets])

    # path of the `dagster` module on the filesystem
    dagster_module_path = os.path.normpath(file_relative_path(__file__, "../../")) + "/"

    # path of the current file relative to the `dagster` module root
    path_in_module = "dagster_tests/asset_defs_tests/"

    # code origin format is
    # {path to module}:{path to file relative to module root}:{line number}
    expected_origins = {
        "james_brown": dagster_module_path + ":" + path_in_module + "asset_package/__init__.py:12",
        "chuck_berry": (
            dagster_module_path + ":" + path_in_module + "asset_package/module_with_assets.py:11"
        ),
        "little_richard": (
            dagster_module_path + ":" + path_in_module + "asset_package/__init__.py:4"
        ),
        "fats_domino": dagster_module_path + ":" + path_in_module + "asset_package/__init__.py:16",
        "miles_davis": (
            dagster_module_path
            + ":"
            + path_in_module
            + "asset_package/asset_subpackage/another_module_with_assets.py:6"
        ),
    }

    for asset in collection_1:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.op.name
            assert op_name in expected_origins, f"Missing expected origin for op {op_name}"
            assert asset.op.tags[CODE_ORIGIN_TAG_NAME] == expected_origins[op_name]
