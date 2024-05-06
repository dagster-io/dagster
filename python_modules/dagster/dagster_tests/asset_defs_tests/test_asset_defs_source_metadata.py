import os
from typing import cast

from dagster import AssetsDefinition, load_assets_from_modules
from dagster._core.definitions.metadata import (
    LocalFileCodeReference,
    SourceControlCodeReference,
    link_to_source_control,
    with_source_code_references,
)
from dagster._utils import file_relative_path

# path of the `dagster` package on the filesystem
DAGSTER_PACKAGE_PATH = os.path.normpath(file_relative_path(__file__, "../../"))
GIT_ROOT_PATH = os.path.normpath(os.path.join(DAGSTER_PACKAGE_PATH, "../../"))

# path of the current file relative to the `dagster` package root
PATH_IN_PACKAGE = "/dagster_tests/asset_defs_tests/"

# {path to module}:{path to file relative to module root}:{line number}
EXPECTED_ORIGINS = {
    "james_brown": DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:12",
    "chuck_berry": (
        DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/module_with_assets.py:16"
    ),
    "little_richard": (DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:4"),
    "fats_domino": DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:16",
    "miles_davis": (
        DAGSTER_PACKAGE_PATH
        + PATH_IN_PACKAGE
        + "asset_package/asset_subpackage/another_module_with_assets.py:6"
    ),
}


def test_asset_code_origins() -> None:
    from dagster_tests.asset_defs_tests import asset_package

    from .asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])

    for asset in collection:
        if isinstance(asset, AssetsDefinition):
            for key in asset.keys:
                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it
                if asset.op.name == "chuck_berry":
                    assert "dagster/code_references" in asset.metadata_by_key[key]
                else:
                    assert "dagster/code_references" not in asset.metadata_by_key[key]

    collection_with_source_metadata = with_source_code_references(collection)

    for asset in collection_with_source_metadata:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.op.name
            assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

            expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")

            for key in asset.keys:
                assert "dagster/code_references" in asset.metadata_by_key[key]

                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it, which coexists with the automatically attached metadata
                if op_name == "chuck_berry":
                    assert (
                        len(asset.metadata_by_key[key]["dagster/code_references"].code_references)
                        == 2
                    )
                else:
                    assert (
                        len(asset.metadata_by_key[key]["dagster/code_references"].code_references)
                        == 1
                    )

                assert isinstance(
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    LocalFileCodeReference,
                )
                meta = cast(
                    LocalFileCodeReference,
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                )

                assert meta.file_path == expected_file_path
                assert meta.line_number == int(expected_line_number)


def test_asset_code_origins_source_control() -> None:
    from dagster_tests.asset_defs_tests import asset_package

    from .asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])

    for asset in collection:
        if isinstance(asset, AssetsDefinition):
            for key in asset.keys:
                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it
                if asset.op.name == "chuck_berry":
                    assert "dagster/code_references" in asset.metadata_by_key[key]
                else:
                    assert "dagster/code_references" not in asset.metadata_by_key[key]

    collection_with_source_metadata = with_source_code_references(collection)
    collection_with_source_control_metadata = link_to_source_control(
        collection_with_source_metadata,
        source_control_url="https://github.com/dagster-io/dagster",
        source_control_branch="master",
        repository_root_absolute_path=GIT_ROOT_PATH,
    )

    for asset in collection_with_source_control_metadata:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.op.name
            assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

            expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")

            for key in asset.keys:
                assert "dagster/code_references" in asset.metadata_by_key[key]

                assert isinstance(
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    SourceControlCodeReference,
                )
                meta = cast(
                    SourceControlCodeReference,
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                )

                assert meta.source_control_url == (
                    "https://github.com/dagster-io/dagster/tree/master/python_modules/dagster"
                    + (expected_file_path[len(DAGSTER_PACKAGE_PATH) :])
                )
                assert meta.line_number == int(expected_line_number)
