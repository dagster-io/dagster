import inspect
import os
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Sequence,
    Union,
)

import pydantic

import dagster._check as check
from dagster._annotations import experimental
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
    line_number: int
    label: Optional[str] = None


@experimental
@whitelist_for_serdes
class CodeReferencesMetadataValue(DagsterModel, MetadataValue["CodeReferencesMetadataValue"]):
    """Metadata value type which represents source locations (locally or otherwise)
    of the asset in question. For example, the file path and line number where the
    asset is defined.

    Attributes:
        sources (List[LocalFileCodeReference]):
            A list of code references for the asset, such as file locations or
            references to source control.
    """

    code_references: List[LocalFileCodeReference]

    @property
    def value(self) -> "CodeReferencesMetadataValue":
        return self


def source_path_from_fn(fn: Callable[..., Any]) -> Optional[LocalFileCodeReference]:
    cwd = os.getcwd()

    origin_file = os.path.abspath(os.path.join(cwd, inspect.getsourcefile(fn)))  # type: ignore
    origin_file = check.not_none(origin_file)
    origin_line = inspect.getsourcelines(fn)[1]

    return LocalFileCodeReference(file_path=origin_file, line_number=origin_line)


class CodeReferencesMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to asset definitions and which specify the location where
    source code for the asset can be found.
    """

    code_references: CodeReferencesMetadataValue

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
    source_path = source_path_from_fn(base_fn)

    if source_path:
        sources = [source_path]

        for key in assets_def.keys:
            # defer to any existing metadata
            sources_for_asset = [*sources]
            try:
                existing_source_code_metadata = CodeReferencesMetadataSet.extract(
                    metadata_by_key.get(key, {})
                )
                sources_for_asset = [
                    *existing_source_code_metadata.code_references.code_references,
                    *sources,
                ]
            except pydantic.ValidationError:
                pass

            metadata_by_key[key] = {
                **metadata_by_key.get(key, {}),
                **CodeReferencesMetadataSet(
                    code_references=CodeReferencesMetadataValue(code_references=sources_for_asset)
                ),
            }

    return assets_def.with_attributes(metadata_by_key=metadata_by_key)


@experimental
def with_source_code_references(
    assets_defs: Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]],
) -> Sequence[Union["AssetsDefinition", "SourceAsset", "CacheableAssetsDefinition"]]:
    """Wrapper function which attaches source code metadata to the provided asset definitions.

    Args:
        assets_defs (Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]):
            The asset definitions to which source code metadata should be attached.

    Returns:
        Sequence[AssetsDefinition]: The asset definitions with source code metadata attached.
    """
    return [_with_code_source_single_definition(assets_def) for assets_def in assets_defs]
