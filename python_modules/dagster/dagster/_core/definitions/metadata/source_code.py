import inspect
import os
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from dagster_shared.dagster_model import DagsterModel
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import beta, public
from dagster._core.definitions.metadata.metadata_set import (
    NamespacedMetadataSet as NamespacedMetadataSet,
    TableMetadataSet as TableMetadataSet,
)
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.assets_definition import (
        AssetsDefinition,
        AssetSpec,
        SourceAsset,
    )
    from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
        CacheableAssetsDefinition,
    )

DEFAULT_SOURCE_FILE_KEY = "asset_definition"


@beta
@whitelist_for_serdes
class LocalFileCodeReference(DagsterModel):
    """Represents a local file source location."""

    file_path: str
    line_number: Optional[int] = None
    label: Optional[str] = None

    @property
    def source(self) -> str:
        return f"{self.file_path}:{self.line_number}" if self.line_number else self.file_path


@beta
@whitelist_for_serdes
class UrlCodeReference(DagsterModel):
    """Represents a source location which points at a URL, for example
    in source control.
    """

    url: str
    label: Optional[str] = None

    @property
    def source(self) -> str:
        return self.url


CodeReference: TypeAlias = Union[LocalFileCodeReference, UrlCodeReference]


@beta
@whitelist_for_serdes
class CodeReferencesMetadataValue(DagsterModel, MetadataValue["CodeReferencesMetadataValue"]):  # pyright: ignore[reportIncompatibleMethodOverride]
    """Metadata value type which represents source locations (locally or otherwise)
    of the asset in question. For example, the file path and line number where the
    asset is defined.

    Args:
        sources (List[Union[LocalFileCodeReference, SourceControlCodeReference]]):
            A list of code references for the asset, such as file locations or
            references to source control.
    """

    code_references: list[CodeReference]

    @property
    def value(self) -> "CodeReferencesMetadataValue":
        return self


def local_source_path_from_fn(fn: Callable[..., Any]) -> Optional[LocalFileCodeReference]:
    cwd = os.getcwd()

    origin_file = os.path.abspath(os.path.join(cwd, inspect.getsourcefile(fn)))  # type: ignore
    origin_file = check.not_none(origin_file)
    origin_line = inspect.getsourcelines(fn)[1]

    return LocalFileCodeReference(file_path=origin_file, line_number=origin_line)


def merge_code_references(
    asset_spec: "AssetSpec",
    new_code_references: Sequence[CodeReference],
) -> "AssetSpec":
    existing_references_meta = CodeReferencesMetadataSet.extract(asset_spec.metadata)
    references = (
        existing_references_meta.code_references.code_references
        if existing_references_meta.code_references
        else []
    )

    return asset_spec.replace_attributes(
        metadata={
            **asset_spec.metadata,
            **CodeReferencesMetadataSet(
                code_references=CodeReferencesMetadataValue(
                    code_references=[
                        *references,
                        *new_code_references,
                    ],
                )
            ),
        }
    )


class CodeReferencesMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to asset definitions and which specify the location where
    source code for the asset can be found.
    """

    code_references: Optional[CodeReferencesMetadataValue] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"


def _with_code_source_single_definition(
    assets_def: Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"],
) -> Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

    # SourceAsset and AssetSpec don't have an op definition to point to - cacheable assets
    # will be supported eventually but are a bit trickier
    if not isinstance(assets_def, AssetsDefinition):
        return assets_def

    metadata_by_key = dict(assets_def.metadata_by_key) or {}

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
    from dagster._core.definitions.graph_definition import GraphDefinition
    from dagster._core.definitions.op_definition import OpDefinition

    base_fn = None
    if isinstance(assets_def.node_def, OpDefinition):
        base_fn = (
            assets_def.node_def.compute_fn.decorated_fn
            if isinstance(assets_def.node_def.compute_fn, DecoratedOpFunction)
            else assets_def.node_def.compute_fn
        )
    elif isinstance(assets_def.node_def, GraphDefinition):
        # For graph-backed assets, point to the composition fn, e.g. the
        # function decorated by @graph_asset
        base_fn = assets_def.node_def.composition_fn

    if not base_fn:
        return assets_def

    source_path = local_source_path_from_fn(base_fn)

    if source_path:
        sources = [source_path]

        for key in assets_def.keys:
            # merge with any existing metadata
            existing_source_code_metadata = CodeReferencesMetadataSet.extract(
                metadata_by_key.get(key, {})
            )
            existing_code_references = (
                existing_source_code_metadata.code_references.code_references
                if existing_source_code_metadata.code_references
                else []
            )
            sources_for_asset: list[Union[LocalFileCodeReference, UrlCodeReference]] = [
                *existing_code_references,
                *sources,
            ]

            metadata_by_key[key] = {
                **metadata_by_key.get(key, {}),
                **CodeReferencesMetadataSet(
                    code_references=CodeReferencesMetadataValue(code_references=sources_for_asset)
                ),
            }

    return assets_def.map_asset_specs(
        lambda spec: spec.replace_attributes(metadata=metadata_by_key[spec.key])
    )


@beta
class FilePathMapping(ABC):
    """Base class which defines a file path mapping function. These functions are used to map local file paths
    to their corresponding paths in a source control repository.

    In many cases where a source control repository is reproduced exactly on a local machine, the included
    AnchorBasedFilePathMapping class can be used to specify a direct mapping between the local file paths and the
    repository paths. However, in cases where the repository structure differs from the local structure, a custom
    mapping function can be provided to handle these cases.
    """

    @public
    @abstractmethod
    def convert_to_source_control_path(self, local_path: Path) -> str:
        """Maps a local file path to the corresponding path in a source control repository.

        Args:
            local_path (Path): The local file path to map.

        Returns:
            str: The corresponding path in the hosted source control repository, relative to the repository root.
        """


@beta
@dataclass
class AnchorBasedFilePathMapping(FilePathMapping):
    """Specifies the mapping between local file paths and their corresponding paths in a source control repository,
    using a specific file "anchor" as a reference point. All other paths are calculated relative to this anchor file.

    For example, if the chosen anchor file is `/Users/dagster/Documents/python_modules/my_module/my-module/__init__.py`
    locally, and `python_modules/my_module/my-module/__init__.py` in a source control repository, in order to map a
    different file `/Users/dagster/Documents/python_modules/my_module/my-module/my_asset.py` to the repository path,
    the mapping function will position the file in the repository relative to the anchor file's position in the repository,
    resulting in `python_modules/my_module/my-module/my_asset.py`.

    Args:
        local_file_anchor (Path): The path to a local file that is present in the repository.
        file_anchor_path_in_repository (str): The path to the anchor file in the repository.

    Example:
        .. code-block:: python

            mapping_fn = AnchorBasedFilePathMapping(
                local_file_anchor=Path(__file__),
                file_anchor_path_in_repository="python_modules/my_module/my-module/__init__.py",
            )
    """

    local_file_anchor: Path
    file_anchor_path_in_repository: str

    @public
    def convert_to_source_control_path(self, local_path: Path) -> str:
        """Maps a local file path to the corresponding path in a source control repository
        based on the anchor file and its corresponding path in the repository.

        Args:
            local_path (Path): The local file path to map.

        Returns:
            str: The corresponding path in the hosted source control repository, relative to the repository root.
        """
        path_from_anchor_to_target = os.path.relpath(
            local_path,
            self.local_file_anchor,
        )
        return os.path.normpath(
            os.path.join(
                self.file_anchor_path_in_repository,
                path_from_anchor_to_target,
            )
        )


def convert_local_path_to_git_path(
    base_git_url: str,
    file_path_mapping: FilePathMapping,
    local_path: LocalFileCodeReference,
) -> UrlCodeReference:
    source_file_from_repo_root = file_path_mapping.convert_to_source_control_path(
        Path(local_path.file_path)
    )
    line_number_suffix = f"#L{local_path.line_number}" if local_path.line_number else ""

    return UrlCodeReference(
        url=f"{base_git_url}/{source_file_from_repo_root}{line_number_suffix}",
        label=local_path.label,
    )


def _convert_local_path_to_git_path_single_definition(
    base_git_url: str,
    file_path_mapping: FilePathMapping,
    assets_def: Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"],
) -> Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

    # SourceAsset doesn't have an op definition to point to - cacheable assets
    # will be supported eventually but are a bit trickier
    if not isinstance(assets_def, AssetsDefinition):
        return assets_def

    metadata_by_key = dict(assets_def.metadata_by_key) or {}

    for key in assets_def.keys:
        existing_source_code_metadata = CodeReferencesMetadataSet.extract(
            metadata_by_key.get(key, {})
        )
        if not existing_source_code_metadata.code_references:
            continue

        sources_for_asset: list[Union[LocalFileCodeReference, UrlCodeReference]] = [
            convert_local_path_to_git_path(
                base_git_url,
                file_path_mapping,
                source,
            )
            if isinstance(source, LocalFileCodeReference)
            else source
            for source in existing_source_code_metadata.code_references.code_references
        ]

        metadata_by_key[key] = {
            **metadata_by_key.get(key, {}),
            **CodeReferencesMetadataSet(
                code_references=CodeReferencesMetadataValue(code_references=sources_for_asset)
            ),
        }

    return assets_def.map_asset_specs(
        lambda spec: spec.replace_attributes(metadata=metadata_by_key[spec.key])
    )


def _build_github_url(url: str, branch: str) -> str:
    return f"{url}/tree/{branch}"


def _build_gitlab_url(url: str, branch: str) -> str:
    return f"{url}/-/tree/{branch}"


@beta
def link_code_references_to_git(
    assets_defs: Sequence[
        Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]
    ],
    git_url: str,
    git_branch: str,
    file_path_mapping: FilePathMapping,
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]]:
    """Wrapper function which converts local file path code references to source control URLs
    based on the provided source control URL and branch.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source control metadata should be attached.
            Only assets with local file code references (such as those created by
            `with_source_code_references`) will be converted.
        git_url (str): The base URL for the source control system. For example,
            "https://github.com/dagster-io/dagster".
        git_branch (str): The branch in the source control system, such as "master".
        file_path_mapping (FilePathMapping):
            Specifies the mapping between local file paths and their corresponding paths in a source control repository.
            Simple usage is to provide a `AnchorBasedFilePathMapping` instance, which specifies an anchor file in the
            repository and the corresponding local file path, which is extrapolated to all other local file paths.
            Alternatively, a custom function can be provided which takes a local file path and returns the corresponding
            path in the repository, allowing for more complex mappings.

    Example:
        .. code-block:: python

                Definitions(
                    assets=link_code_references_to_git(
                        with_source_code_references([my_dbt_assets]),
                        git_url="https://github.com/dagster-io/dagster",
                        git_branch="master",
                        file_path_mapping=AnchorBasedFilePathMapping(
                            local_file_anchor=Path(__file__),
                            file_anchor_path_in_repository="python_modules/my_module/my-module/__init__.py",
                        ),
                    )
                )
    """
    if "gitlab" in git_url:
        git_url = _build_gitlab_url(git_url, git_branch)
    elif "github.com" in git_url:
        git_url = _build_github_url(git_url, git_branch)
    else:
        raise ValueError(
            "Invalid `git_url`."
            " Only GitHub and GitLab are supported for linking to source control at this time."
        )

    return [
        _convert_local_path_to_git_path_single_definition(
            base_git_url=git_url,
            file_path_mapping=file_path_mapping,
            assets_def=assets_def,
        )
        for assets_def in assets_defs
    ]


@beta
def with_source_code_references(
    assets_defs: Sequence[
        Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]
    ],
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition", "AssetSpec"]]:
    """Wrapper function which attaches local code reference metadata to the provided asset definitions.
    This points to the filepath and line number where the asset body is defined.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source code metadata should be attached.

    Returns:
        Sequence[AssetsDefinition]: The asset definitions with source code metadata attached.
    """
    return [_with_code_source_single_definition(assets_def) for assets_def in assets_defs]
