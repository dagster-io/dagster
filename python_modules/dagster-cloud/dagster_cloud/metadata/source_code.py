import os
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Union

from dagster import DagsterInvariantViolationError
from dagster._annotations import beta
from dagster._core.definitions.metadata import (
    AnchorBasedFilePathMapping,
    link_code_references_to_git,
)
from dagster._core.definitions.metadata.source_code import FilePathMapping
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

if TYPE_CHECKING:
    from dagster import AssetsDefinition, AssetSpec, SourceAsset
    from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
        CacheableAssetsDefinition,
    )

import sys


def _locate_git_root() -> Path | None:
    try:
        code_origin = LoadableTargetOrigin.get()
    except DagsterInvariantViolationError:
        return None

    # get module matching code_origin.module_name
    module_or_pkg_name = code_origin.module_name or code_origin.package_name
    if module_or_pkg_name:
        module = sys.modules.get(module_or_pkg_name)
        if module:
            code_origin_filepath = module.__file__
    elif code_origin.python_file:
        code_origin_filepath = code_origin.python_file

    if not code_origin_filepath:
        return None
    current_dir = Path(code_origin_filepath)
    for parent in current_dir.parents:
        if (parent / ".git").exists():
            return parent
    return None


@beta
def link_code_references_to_git_if_cloud(
    assets_defs: Sequence[
        Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]
    ],
    git_url: str | None = None,
    git_branch: str | None = None,
    file_path_mapping: FilePathMapping | None = None,
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]]:
    """Wrapper function which converts local file path code references to hosted git URLs
    if running in a Dagster Plus cloud environment. This is determined by the presence of
    the `DAGSTER_CLOUD_DEPLOYMENT_NAME` environment variable. When running in any other context,
    the local file references are left as is.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source control metadata should be attached.
            Only assets with local file code references (such as those created by
            `with_source_code_references`) will be converted.
        git_url (Optional[str]): Override base URL for the source control system. By default,
            inferred from the `DAGSTER_CLOUD_GIT_URL` environment variable provided by cloud.
            For example, "https://github.com/dagster-io/dagster".
        git_branch (str): Override branch in the source control system, such as "master".
            Defaults to the `DAGSTER_CLOUD_GIT_SHA` or `DAGSTER_CLOUD_GIT_BRANCH` environment variable.
        file_path_mapping (Optional[FilePathMapping]):
            Specifies the mapping between local file paths and their corresponding paths in a source control repository.
            If None, the function will attempt to infer the git root of the repository and use that as a reference
            point. Simple usage is to provide a `AnchorBasedFilePathMapping` instance, which specifies an anchor file in the
            repository and the corresponding local file path, which is extrapolated to all other local file paths.
            Alternatively, a mapping can be provided which takes a local file path and returns the corresponding path in
            the repository, allowing for more complex mappings.


    Examples:
        Basic usage:
        .. code-block:: python
                defs = Definitions(
                    assets=link_code_references_to_git_if_cloud(
                        with_source_code_references([my_dbt_assets]),
                    )
                )

        Provide custom mapping for repository file paths, e.g. if local files no longer match
        the repository structure:
        .. code-block:: python
                defs = Definitions(
                    assets=link_code_references_to_git_if_cloud(
                        with_source_code_references([my_dbt_assets]),
                        file_path_mapping=AnchorBasedFilePathMapping(
                            local_file_anchor=Path(__file__),
                            file_anchor_path_in_repository="python_modules/my_module/my-module/__init__.py",
                        ),
                    )
                )
    """
    is_dagster_cloud = os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME") is not None

    if not is_dagster_cloud:
        return assets_defs

    git_url = git_url or os.getenv("DAGSTER_CLOUD_GIT_URL")
    git_branch = (
        git_branch or os.getenv("DAGSTER_CLOUD_GIT_SHA") or os.getenv("DAGSTER_CLOUD_GIT_BRANCH")
    )

    if not git_url or not git_branch:
        raise ValueError(
            "Detected that this is a Dagster Cloud deployment, but"
            " could not infer source control information for this repository. Please provide"
            " values for `git_url` and `git_branch`."
        )

    if not file_path_mapping:
        git_root = _locate_git_root()
        if not git_root:
            raise ValueError(
                "Detected that this is a Dagster Cloud deployment, but"
                " could not infer the git root for the repository. Please provide a value for "
                "`file_path_mapping`."
            )
        file_path_mapping = AnchorBasedFilePathMapping(
            local_file_anchor=git_root,
            file_anchor_path_in_repository="",
        )

    return link_code_references_to_git(
        assets_defs=assets_defs,
        git_url=git_url,
        git_branch=git_branch,
        file_path_mapping=file_path_mapping,
    )
