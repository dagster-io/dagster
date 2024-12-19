import os
from pathlib import Path
from typing import cast

from dagster import AssetsDefinition, load_assets_from_modules
from dagster._core.definitions.metadata import (
    LocalFileCodeReference,
    UrlCodeReference,
    with_source_code_references,
)
from dagster._core.definitions.metadata.source_code import (
    AnchorBasedFilePathMapping,
    FilePathMapping,
    link_code_references_to_git,
)
from dagster._utils import file_relative_path

# path of the `dagster` package on the filesystem
DAGSTER_PACKAGE_PATH = os.path.normpath(file_relative_path(__file__, "../../"))
GIT_ROOT_PATH = os.path.normpath(os.path.join(DAGSTER_PACKAGE_PATH, "../../"))

# path of the current file relative to the `dagster` package root
PATH_IN_PACKAGE = "/dagster_tests/definitions_tests/module_loader_tests/"

# {path to module}:{path to file relative to module root}:{line number}
EXPECTED_ORIGINS = {
    "james_brown": DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:13",
    "chuck_berry": (
        DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/module_with_assets.py:19"
    ),
    "little_richard": (DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:5"),
    "fats_domino": DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:17",
    "miles_davis": (
        DAGSTER_PACKAGE_PATH
        + PATH_IN_PACKAGE
        + "asset_package/asset_subpackage/another_module_with_assets.py:6"
    ),
    "graph_backed_asset": (
        DAGSTER_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/module_with_assets.py:42"
    ),
}


def test_asset_code_origins() -> None:
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])

    for asset in collection:
        if isinstance(asset, AssetsDefinition):
            for key in asset.keys:
                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it
                if asset.node_def.name == "chuck_berry":
                    assert "dagster/code_references" in asset.metadata_by_key[key]
                else:
                    assert "dagster/code_references" not in asset.metadata_by_key[key]

    collection_with_source_metadata = with_source_code_references(collection)

    for asset in collection_with_source_metadata:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.node_def.name

            assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

            expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")

            for key in asset.keys:
                assert "dagster/code_references" in asset.specs_by_key[key].metadata

                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it, which coexists with the automatically attached metadata
                if op_name == "chuck_berry":
                    assert (
                        len(
                            asset.specs_by_key[key]
                            .metadata["dagster/code_references"]
                            .code_references
                        )
                        == 2
                    )
                else:
                    assert (
                        len(
                            asset.specs_by_key[key]
                            .metadata["dagster/code_references"]
                            .code_references
                        )
                        == 1
                    )

                assert isinstance(
                    asset.specs_by_key[key].metadata["dagster/code_references"].code_references[-1],
                    LocalFileCodeReference,
                )
                meta = cast(
                    LocalFileCodeReference,
                    asset.specs_by_key[key].metadata["dagster/code_references"].code_references[-1],
                )

                assert meta.file_path == expected_file_path
                assert meta.line_number == int(expected_line_number)


def test_asset_code_origins_source_control() -> None:
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])

    for asset in collection:
        if isinstance(asset, AssetsDefinition):
            for key in asset.keys:
                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it
                if asset.node_def.name == "chuck_berry":
                    assert "dagster/code_references" in asset.specs_by_key[key].metadata
                else:
                    assert "dagster/code_references" not in asset.specs_by_key[key].metadata

    collection_with_source_metadata = with_source_code_references(collection)

    collection_with_source_control_metadata = link_code_references_to_git(
        collection_with_source_metadata,
        git_url="https://github.com/dagster-io/dagster",
        git_branch="master",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(GIT_ROOT_PATH), file_anchor_path_in_repository=""
        ),
    )

    for asset in collection_with_source_control_metadata:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.node_def.name

            assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

            expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")

            for key in asset.keys:
                assert "dagster/code_references" in asset.specs_by_key[key].metadata

                assert isinstance(
                    asset.specs_by_key[key].metadata["dagster/code_references"].code_references[-1],
                    UrlCodeReference,
                )
                meta = cast(
                    UrlCodeReference,
                    asset.specs_by_key[key].metadata["dagster/code_references"].code_references[-1],
                )

                assert meta.url == (
                    "https://github.com/dagster-io/dagster/tree/master/python_modules/dagster"
                    + (expected_file_path[len(DAGSTER_PACKAGE_PATH) :])
                    + f"#L{expected_line_number}"
                )


def test_asset_code_origins_source_control_custom_mapping() -> None:
    # test custom source_control_file_path_mapping fn

    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])

    for asset in collection:
        if isinstance(asset, AssetsDefinition):
            for key in asset.keys:
                # `chuck_berry` is the only asset with source code metadata manually
                # attached to it
                if asset.node_def.name == "chuck_berry":
                    assert "dagster/code_references" in asset.metadata_by_key[key]
                else:
                    assert "dagster/code_references" not in asset.metadata_by_key[key]

    collection_with_source_metadata = with_source_code_references(collection)

    class CustomFilePathMapping(FilePathMapping):
        def convert_to_source_control_path(self, local_path: Path) -> str:
            return (
                "override.py"
                if os.fspath(local_path).endswith("module_with_assets.py")
                else os.path.normpath(os.path.relpath(local_path, GIT_ROOT_PATH))
            )

    collection_with_source_control_metadata = link_code_references_to_git(
        collection_with_source_metadata,
        git_url="https://github.com/dagster-io/dagster",
        git_branch="master",
        file_path_mapping=CustomFilePathMapping(),
    )

    for asset in collection_with_source_control_metadata:
        if isinstance(asset, AssetsDefinition):
            op_name = asset.node_def.name

            assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

            expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")
            expected_url = (
                "https://github.com/dagster-io/dagster/tree/master/python_modules/dagster"
                + (expected_file_path[len(DAGSTER_PACKAGE_PATH) :])
                + f"#L{expected_line_number}"
            )
            if expected_file_path.endswith("module_with_assets.py"):
                expected_url = (
                    "https://github.com/dagster-io/dagster/tree/master/override.py"
                    + f"#L{expected_line_number}"
                )

            for key in asset.keys:
                assert "dagster/code_references" in asset.metadata_by_key[key]

                assert isinstance(
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    UrlCodeReference,
                )
                meta = cast(
                    UrlCodeReference,
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                )

                assert meta.url == expected_url
