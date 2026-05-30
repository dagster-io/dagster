import os
from pathlib import Path
from typing import cast

import pytest
from dagster import AssetsDefinition, load_assets_from_modules
from dagster._core.definitions.metadata import (
    LocalFileCodeReference,
    UrlCodeReference,
    with_source_code_references,
)
from dagster._core.definitions.metadata.source_code import FilePathMapping
from dagster._core.types.loadable_target_origin import (
    LoadableTargetOrigin,
    enter_loadable_target_origin_load_context,
)
from dagster._utils import file_relative_path
from dagster._utils.env import environ
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

# path of the `dagster` package on the filesystem
DAGSTER_CLOUD_PACKAGE_PATH = os.path.normpath(file_relative_path(__file__, "../../"))
GIT_ROOT_PATH = os.path.normpath(os.path.join(DAGSTER_CLOUD_PACKAGE_PATH, "../../../"))

# path of the current file relative to the `dagster` package root
PATH_IN_PACKAGE = "/dagster_cloud_tests/metadata_tests/"

# {path to module}:{path to file relative to module root}:{line number}
EXPECTED_ORIGINS = {
    "james_brown": DAGSTER_CLOUD_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:12",
    "chuck_berry": (
        DAGSTER_CLOUD_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/module_with_assets.py:18"
    ),
    "little_richard": (
        DAGSTER_CLOUD_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:4"
    ),
    "fats_domino": DAGSTER_CLOUD_PACKAGE_PATH + PATH_IN_PACKAGE + "asset_package/__init__.py:16",
    "miles_davis": (
        DAGSTER_CLOUD_PACKAGE_PATH
        + PATH_IN_PACKAGE
        + "asset_package/asset_subpackage/another_module_with_assets.py:6"
    ),
}


def test_link_code_references_to_git_if_cloud_no_cloud_context() -> None:
    from dagster_cloud_tests.metadata_tests import asset_package
    from dagster_cloud_tests.metadata_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])
    collection_with_source_metadata = with_source_code_references(collection)
    # should be a no-op since we don't have the necessary environment variables set
    collection_with_potential_source_control_metadata = link_code_references_to_git_if_cloud(
        collection_with_source_metadata
    )

    for asset in collection_with_potential_source_control_metadata:
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
                    "LocalFileCodeReference",
                    asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                )

                assert meta.file_path == expected_file_path
                assert meta.line_number == int(expected_line_number)


# paramterize github gitlab
@pytest.mark.parametrize(
    "source_control_url, source_control_branch_base",
    [
        pytest.param(
            "https://github.com/dagster-io/dagster",
            "https://github.com/dagster-io/dagster/tree/master",
            id="github",
        ),
        pytest.param(
            "https://gitlab.com/dagster-io/dagster",
            "https://gitlab.com/dagster-io/dagster/-/tree/master",
            id="gitlab",
        ),
    ],
)
def test_link_code_references_to_git_if_cloud_cloud_context(
    source_control_url: str, source_control_branch_base: str
) -> None:
    from dagster_cloud_tests.metadata_tests import asset_package
    from dagster_cloud_tests.metadata_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])
    collection_with_source_metadata = with_source_code_references(collection)

    # Setup the cloud context so that our code references are linked to source control
    with (
        environ(
            {
                "DAGSTER_CLOUD_DEPLOYMENT_NAME": "prod",
                "DAGSTER_CLOUD_GIT_URL": source_control_url,
                "DAGSTER_CLOUD_GIT_BRANCH": "master",
            }
        ),
        enter_loadable_target_origin_load_context(
            loadable_target_origin=LoadableTargetOrigin(python_file=__file__)
        ),
    ):
        # should link to source control since we have the necessary environment variables set
        collection_with_source_control_metadata = link_code_references_to_git_if_cloud(
            collection_with_source_metadata,
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
                        UrlCodeReference,
                    )
                    meta = cast(
                        "UrlCodeReference",
                        asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    )

                    assert meta.url == (
                        f"{source_control_branch_base}/dagster-oss/python_modules/dagster-cloud"
                        + (expected_file_path[len(DAGSTER_CLOUD_PACKAGE_PATH) :])
                        + f"#L{expected_line_number}"
                    )


def test_link_code_references_to_git_if_cloud_partial_cloud_context() -> None:
    from dagster_cloud_tests.metadata_tests import asset_package
    from dagster_cloud_tests.metadata_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])
    collection_with_source_metadata = with_source_code_references(collection)

    # Setup the cloud context but do not provide the other necessary environment variables
    with (
        environ(
            {
                "DAGSTER_CLOUD_DEPLOYMENT_NAME": "prod",
            }
        ),
        enter_loadable_target_origin_load_context(
            loadable_target_origin=LoadableTargetOrigin(python_file=__file__)
        ),
    ):
        # We lack the branch/url environment variables so this should raise an error
        with pytest.raises(ValueError):
            link_code_references_to_git_if_cloud(
                collection_with_source_metadata,
            )


def test_link_code_references_to_git_if_cloud_override_cloud_context() -> None:
    from dagster_cloud_tests.metadata_tests import asset_package
    from dagster_cloud_tests.metadata_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])
    collection_with_source_metadata = with_source_code_references(collection)

    # Setup the cloud context so that our code references are linked to source control
    with (
        environ({"DAGSTER_CLOUD_DEPLOYMENT_NAME": "prod"}),
        enter_loadable_target_origin_load_context(
            loadable_target_origin=LoadableTargetOrigin(python_file=__file__)
        ),
    ):
        # should link to source control despite missing the necessary environment variables
        # because we provide the necessary source control information as arguments
        collection_with_source_control_metadata = link_code_references_to_git_if_cloud(
            collection_with_source_metadata,
            git_url="https://github.com/dagster-io/other-repo",
            git_branch="main",
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
                        UrlCodeReference,
                    )
                    meta = cast(
                        "UrlCodeReference",
                        asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    )

                    assert meta.url == (
                        "https://github.com/dagster-io/other-repo/tree/main/dagster-oss/python_modules/dagster-cloud"
                        + (expected_file_path[len(DAGSTER_CLOUD_PACKAGE_PATH) :])
                        + f"#L{expected_line_number}"
                    )


def test_link_code_references_to_git_if_cloud_override_cloud_context_mapping() -> None:
    from dagster_cloud_tests.metadata_tests import asset_package
    from dagster_cloud_tests.metadata_tests.asset_package import module_with_assets

    collection = load_assets_from_modules([asset_package, module_with_assets])
    collection_with_source_metadata = with_source_code_references(collection)

    # Setup the cloud context so that our code references are linked to source control
    with (
        environ({"DAGSTER_CLOUD_DEPLOYMENT_NAME": "prod"}),
        enter_loadable_target_origin_load_context(
            loadable_target_origin=LoadableTargetOrigin(python_file=__file__)
        ),
    ):
        # should link to source control despite missing the necessary environment variables
        # because we provide the necessary source control information as arguments

        class _FilePathMapping(FilePathMapping):
            def convert_to_source_control_path(self, local_path: Path) -> str:
                return "override.py"

        collection_with_source_control_metadata = link_code_references_to_git_if_cloud(
            collection_with_source_metadata,
            git_url="https://github.com/dagster-io/other-repo",
            git_branch="main",
            file_path_mapping=_FilePathMapping(),
        )

        for asset in collection_with_source_control_metadata:
            if isinstance(asset, AssetsDefinition):
                op_name = asset.op.name
                assert op_name in EXPECTED_ORIGINS, f"Missing expected origin for op {op_name}"

                _expected_file_path, expected_line_number = EXPECTED_ORIGINS[op_name].split(":")

                for key in asset.keys:
                    assert "dagster/code_references" in asset.metadata_by_key[key]

                    assert isinstance(
                        asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                        UrlCodeReference,
                    )
                    meta = cast(
                        "UrlCodeReference",
                        asset.metadata_by_key[key]["dagster/code_references"].code_references[-1],
                    )

                    assert meta.url.endswith(f"override.py#L{expected_line_number}")
