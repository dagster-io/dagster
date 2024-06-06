import inspect
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, List, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._annotations import deprecated, experimental
from dagster._model import DagsterModel
from dagster._serdes import whitelist_for_serdes

from .metadata_set import (
    NamespacedMetadataSet as NamespacedMetadataSet,
    TableMetadataSet as TableMetadataSet,
)
from .metadata_value import MetadataValue

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
    from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition

DEFAULT_SOURCE_FILE_KEY = "asset_definition"


@experimental
@whitelist_for_serdes
class LocalFileCodeReference(DagsterModel):
    """Represents a local file source location."""

    file_path: str
    line_number: Optional[int] = None
    label: Optional[str] = None


@experimental
@whitelist_for_serdes
class UrlCodeReference(DagsterModel):
    """Represents a source location which points at a URL, for example
    in source control.
    """

    url: str
    label: Optional[str] = None


@experimental
@whitelist_for_serdes
class CodeReferencesMetadataValue(DagsterModel, MetadataValue["CodeReferencesMetadataValue"]):
    """Metadata value type which represents source locations (locally or otherwise)
    of the asset in question. For example, the file path and line number where the
    asset is defined.

    Attributes:
        sources (List[Union[LocalFileCodeReference, SourceControlCodeReference]]):
            A list of code references for the asset, such as file locations or
            references to source control.
    """

    code_references: List[Union[LocalFileCodeReference, UrlCodeReference]]

    @property
    def value(self) -> "CodeReferencesMetadataValue":
        return self


def local_source_path_from_fn(fn: Callable[..., Any]) -> Optional[LocalFileCodeReference]:
    cwd = os.getcwd()

    origin_file = os.path.abspath(os.path.join(cwd, inspect.getsourcefile(fn)))  # type: ignore
    origin_file = check.not_none(origin_file)
    origin_line = inspect.getsourcelines(fn)[1]

    return LocalFileCodeReference(file_path=origin_file, line_number=origin_line)


class CodeReferencesMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to asset definitions and which specify the location where
    source code for the asset can be found.
    """

    code_references: Optional[CodeReferencesMetadataValue] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"


def _with_code_source_single_definition(
    assets_def: Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"],
) -> Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]:
    from dagster._core.definitions.assets import AssetsDefinition

    # SourceAsset doesn't have an op definition to point to - cacheable assets
    # will be supported eventually but are a bit trickier
    if not isinstance(assets_def, AssetsDefinition):
        return assets_def

    metadata_by_key = dict(assets_def.metadata_by_key) or {}

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    base_fn = (
        assets_def.op.compute_fn.decorated_fn
        if isinstance(assets_def.op.compute_fn, DecoratedOpFunction)
        else assets_def.op.compute_fn
    )
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
            sources_for_asset: List[Union[LocalFileCodeReference, UrlCodeReference]] = [
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
        lambda spec: spec._replace(metadata=metadata_by_key[spec.key])
    )


class SourceControlFilePathMapping(NamedTuple):
    """Specifies the mapping between local file paths and their corresponding paths in a source control repository,
    using a specific anchor file as a reference point. All other paths are calculated relative to this anchor file.

    Args:
        local_file_anchor (Path): The path to a local file that is present in the repository.
        file_anchor_path_in_repository (Path): The path to the anchor file in the repository.

    Example:
        .. code-block:: python

            anchor = SourceControlFilePathMapping(
                local_file_anchor=Path(__file__),
                file_anchor_path_in_repository="python_modules/my_module/my-module/__init__.py",
            )
    """

    local_file_anchor: Path
    file_anchor_path_in_repository: str


SourceControlFilePathMappingFn = Callable[[Path], str]


def convert_local_path_to_source_control_path(
    base_source_control_url: str,
    source_control_file_path_mapping_fn: SourceControlFilePathMappingFn,
    local_path: LocalFileCodeReference,
) -> UrlCodeReference:
    source_file_from_repo_root = source_control_file_path_mapping_fn(Path(local_path.file_path))
    line_number_suffix = f"#L{local_path.line_number}" if local_path.line_number else ""

    return UrlCodeReference(
        url=f"{base_source_control_url}/{source_file_from_repo_root}{line_number_suffix}",
        label=local_path.label,
    )


def _convert_local_path_to_source_control_path_single_definition(
    base_source_control_url: str,
    source_control_file_path_mapping_fn: SourceControlFilePathMappingFn,
    assets_def: Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"],
) -> Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]:
    from dagster._core.definitions.assets import AssetsDefinition

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

        sources_for_asset: List[Union[LocalFileCodeReference, UrlCodeReference]] = [
            convert_local_path_to_source_control_path(
                base_source_control_url,
                source_control_file_path_mapping_fn,
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
        lambda spec: spec._replace(metadata=metadata_by_key[spec.key])
    )


def _build_github_url(url: str, branch: str) -> str:
    return f"{url}/tree/{branch}"


def _build_gitlab_url(url: str, branch: str) -> str:
    return f"{url}/-/tree/{branch}"


@experimental
@deprecated(breaking_version="1.8", additional_warn_text="Use `link_to_git` instead.")
def link_to_source_control(
    assets_defs: Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]],
    source_control_url: str,
    source_control_branch: str,
    repository_root_absolute_path: Union[Path, str],
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]]:
    caller_file = Path(inspect.stack()[3].filename).absolute()
    file_anchor_path_in_repository = os.path.relpath(caller_file, repository_root_absolute_path)

    return link_to_git(
        assets_defs=assets_defs,
        source_control_url=source_control_url,
        source_control_branch=source_control_branch,
        source_control_file_path_mapping=SourceControlFilePathMapping(
            local_file_anchor=(caller_file),
            file_anchor_path_in_repository=file_anchor_path_in_repository,
        ),
    )


@experimental
def link_to_git(
    assets_defs: Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]],
    source_control_url: str,
    source_control_branch: str,
    source_control_file_path_mapping: Union[
        SourceControlFilePathMapping, SourceControlFilePathMappingFn
    ],
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]]:
    """Wrapper function which converts local file path code references to source control URLs
    based on the provided source control URL and branch.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source control metadata should be attached.
            Only assets with local file code references (such as those created by
            `with_source_code_references`) will be converted.
        source_control_url (str): The base URL for the source control system. For example,
            "https://github.com/dagster-io/dagster".
        source_control_branch (str): The branch in the source control system, such as "master".
        source_control_file_path_mapping (Union[SourceControlFilePathMapping, SourceControlFilePathMappingFn]):
            Specifies the mapping between local file paths and their corresponding paths in a source control repository.
            Simple usage is to provide a `SourceControlFilePathMapping` instance, which specifies an anchor file in the
            repository and the corresponding local file path, which is extrapolated to all other local file paths.
            Alternatively, a function can be provided which takes a local file path and returns the corresponding path in
            the repository, allowing for more complex mappings.

    Example:
        .. code-block:: python
                defs = Definitions(
                    assets=link_to_git(
                        with_source_code_references([my_dbt_assets]),
                        source_control_url="https://github.com/dagster-io/dagster",
                        source_control_branch="master",
                        source_control_file_path_mapping=SourceControlFilePathMapping(
                            local_file_anchor=Path(__file__),
                            file_anchor_path_in_repository="python_modules/my_module/my-module/__init__.py",
                        ),
                    )
                )
    """
    if "gitlab.com" in source_control_url:
        source_control_url = _build_gitlab_url(source_control_url, source_control_branch)
    elif "github.com" in source_control_url:
        source_control_url = _build_github_url(source_control_url, source_control_branch)
    else:
        raise ValueError(
            "Invalid `source_control_url`."
            " Only GitHub and GitLab are supported for linking to source control at this time."
        )

    _source_control_file_path_mapping: SourceControlFilePathMappingFn
    if isinstance(source_control_file_path_mapping, SourceControlFilePathMapping):

        def resolve_path(local_path: Path) -> str:
            path_from_anchor_to_target = os.path.relpath(
                local_path,
                source_control_file_path_mapping.local_file_anchor,
            )
            return os.path.normpath(
                os.path.join(
                    source_control_file_path_mapping.file_anchor_path_in_repository,
                    path_from_anchor_to_target,
                )
            )

        _source_control_file_path_mapping = resolve_path
    else:
        _source_control_file_path_mapping = source_control_file_path_mapping

    return [
        _convert_local_path_to_source_control_path_single_definition(
            base_source_control_url=source_control_url,
            source_control_file_path_mapping_fn=_source_control_file_path_mapping,
            assets_def=assets_def,
        )
        for assets_def in assets_defs
    ]


@experimental
def with_source_code_references(
    assets_defs: Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]],
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]]:
    """Wrapper function which attaches local code reference metadata to the provided asset definitions.
    This points to the filepath and line number where the asset body is defined.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source code metadata should be attached.

    Returns:
        Sequence[AssetsDefinition]: The asset definitions with source code metadata attached.
    """
    return [_with_code_source_single_definition(assets_def) for assets_def in assets_defs]
