import os
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Dict, Generic, List, NamedTuple, Optional, Union, cast  # noqa: F401, UP035

from dagster_shared.serdes.serdes import (
    FieldSerializer,
    PackableValue,
    UnpackContext,
    WhitelistMap,
    pack_value,
)
from typing_extensions import TypeAlias, TypeVar

import dagster._check as check
from dagster._annotations import PublicAttr, deprecated, deprecated_param
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.metadata_set import (
    NamespacedMetadataSet as NamespacedMetadataSet,
    TableMetadataSet as TableMetadataSet,
)
from dagster._core.definitions.metadata.metadata_value import (
    BoolMetadataValue as BoolMetadataValue,
    DagsterAssetMetadataValue as DagsterAssetMetadataValue,
    DagsterJobMetadataValue as DagsterJobMetadataValue,
    DagsterRunMetadataValue as DagsterRunMetadataValue,
    FloatMetadataValue as FloatMetadataValue,
    IntMetadataValue as IntMetadataValue,
    JsonMetadataValue as JsonMetadataValue,
    MarkdownMetadataValue as MarkdownMetadataValue,
    MetadataValue as MetadataValue,
    NotebookMetadataValue as NotebookMetadataValue,
    NullMetadataValue as NullMetadataValue,
    PathMetadataValue as PathMetadataValue,
    PoolMetadataValue as PoolMetadataValue,
    PythonArtifactMetadataValue as PythonArtifactMetadataValue,
    TableColumnLineageMetadataValue as TableColumnLineageMetadataValue,
    TableMetadataValue as TableMetadataValue,
    TableSchemaMetadataValue as TableSchemaMetadataValue,
    TextMetadataValue as TextMetadataValue,
    TimestampMetadataValue as TimestampMetadataValue,
    UrlMetadataValue as UrlMetadataValue,
)
from dagster._core.definitions.metadata.source_code import (
    DEFAULT_SOURCE_FILE_KEY as DEFAULT_SOURCE_FILE_KEY,
    AnchorBasedFilePathMapping as AnchorBasedFilePathMapping,
    CodeReferencesMetadataSet as CodeReferencesMetadataSet,
    CodeReferencesMetadataValue as CodeReferencesMetadataValue,
    FilePathMapping as FilePathMapping,
    LocalFileCodeReference as LocalFileCodeReference,
    UrlCodeReference as UrlCodeReference,
    link_code_references_to_git as link_code_references_to_git,
    with_source_code_references as with_source_code_references,
)
from dagster._core.definitions.metadata.table import (
    TableColumn as TableColumn,
    TableColumnConstraints as TableColumnConstraints,
    TableColumnDep as TableColumnDep,
    TableColumnLineage as TableColumnLineage,
    TableConstraints as TableConstraints,
    TableRecord as TableRecord,
    TableSchema as TableSchema,
)
from dagster._core.errors import DagsterInvalidMetadata
from dagster._serdes import whitelist_for_serdes
from dagster._utils.warnings import deprecation_warning, normalize_renamed_param

ArbitraryMetadataMapping: TypeAlias = Mapping[str, Any]

RawMetadataValue = Union[
    MetadataValue,
    TableSchema,
    AssetKey,
    os.PathLike,
    dict[Any, Any],
    float,
    int,
    list[Any],
    str,
    datetime,
    None,
]

MetadataMapping: TypeAlias = Mapping[str, MetadataValue]
RawMetadataMapping: TypeAlias = Mapping[str, RawMetadataValue]

T_Packable = TypeVar("T_Packable", bound=PackableValue, default=PackableValue, covariant=True)

# ########################
# ##### NORMALIZATION
# ########################


def normalize_metadata(
    metadata: Mapping[str, RawMetadataValue],
    allow_invalid: bool = False,
) -> Mapping[str, MetadataValue]:
    # This is a stopgap measure to deal with unsupported metadata values, which occur when we try
    # to convert arbitrary metadata (on e.g. OutputDefinition) to a MetadataValue, which is required
    # for serialization. This will cause unsupported values to be silently replaced with a
    # string placeholder.
    normalized_metadata: dict[str, MetadataValue] = {}
    for k, v in metadata.items():
        try:
            normalized_value = normalize_metadata_value(v)
        except DagsterInvalidMetadata as e:
            if allow_invalid:
                deprecation_warning(
                    "Support for arbitrary metadata values",
                    "2.0.0",
                    additional_warn_text=(
                        "In the future, all user-supplied metadata values must be one of"
                        f" {RawMetadataValue}"
                    ),
                    stacklevel=4,  # to get the caller of `normalize_metadata`
                )
                normalized_value = TextMetadataValue(f"[{v.__class__.__name__}] (unserializable)")
            else:
                raise DagsterInvalidMetadata(
                    f'Could not resolve the metadata value for "{k}" to a known type. {e}'
                ) from None
        normalized_metadata[k] = normalized_value

    return normalized_metadata


def has_corresponding_metadata_value_class(obj: Any) -> bool:
    return isinstance(obj, (str, float, bool, int, list, dict, os.PathLike, AssetKey, TableSchema))


def normalize_metadata_value(raw_value: RawMetadataValue) -> "MetadataValue[Any]":
    if isinstance(raw_value, MetadataValue):
        return raw_value
    elif isinstance(raw_value, str):
        return MetadataValue.text(raw_value)
    elif isinstance(raw_value, float):
        return MetadataValue.float(raw_value)
    elif isinstance(raw_value, bool):
        return MetadataValue.bool(raw_value)
    elif isinstance(raw_value, int):
        return MetadataValue.int(raw_value)
    elif isinstance(raw_value, (list, dict)):
        return MetadataValue.json(raw_value)
    elif isinstance(raw_value, os.PathLike):
        return MetadataValue.path(raw_value)
    elif isinstance(raw_value, AssetKey):
        return MetadataValue.asset(raw_value)
    elif isinstance(raw_value, TableSchema):
        return MetadataValue.table_schema(raw_value)
    elif isinstance(raw_value, TableColumnLineage):
        return MetadataValue.column_lineage(raw_value)
    elif raw_value is None:
        return MetadataValue.null()

    raise DagsterInvalidMetadata(
        f"Its type was {type(raw_value)}. Consider wrapping the value with the appropriate "
        "MetadataValue type."
    )


# ########################
# ##### METADATA BACKCOMPAT
# ########################

# Metadata used to be represented as a `List[MetadataEntry]`, but that class has been deleted. But
# we still serialize metadata dicts to the serialized representation of `List[MetadataEntry]` for
# backcompat purposes.


class MetadataFieldSerializer(FieldSerializer):
    """Converts between metadata dict (new) and metadata entries list (old)."""

    storage_name = "metadata_entries"
    loaded_name = "metadata"

    def pack(
        self,
        metadata_dict: Mapping[str, MetadataValue],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Sequence[Mapping[str, Any]]:
        return [
            {
                "__class__": "EventMetadataEntry",
                "label": k,
                # MetadataValue itself can't inherit from NamedTuple and so isn't a PackableValue,
                # but one of its subclasses will always be returned here.
                "entry_data": pack_value(v, whitelist_map, descent_path),  # type: ignore
                "description": None,
            }
            for k, v in metadata_dict.items()
        ]

    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        metadata_entries: list["MetadataEntry"],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> Mapping[str, MetadataValue]:
        return {e.label: e.entry_data for e in metadata_entries}


T_MetadataValue = TypeVar("T_MetadataValue", bound=MetadataValue, covariant=True)


# NOTE: MetadataEntry is no longer accessible via the public API-- all metadata APIs use metadata
# dicts. This clas shas only been preserved to adhere strictly to our backcompat guarantees. It is
# still instantiated in the above `MetadataFieldSerializer` but that can easily be changed.
@deprecated(
    breaking_version="2.0",
    additional_warn_text="Please use a dict with `MetadataValue` values instead.",
)
@deprecated_param(
    param="entry_data", breaking_version="2.0", additional_warn_text="Use `value` instead."
)
@whitelist_for_serdes(storage_name="EventMetadataEntry")
class MetadataEntry(
    NamedTuple(
        "_MetadataEntry",
        [
            ("label", PublicAttr[str]),
            ("description", PublicAttr[Optional[str]]),
            ("entry_data", PublicAttr[MetadataValue]),
        ],
    ),
    Generic[T_MetadataValue],
):
    """A structure for describing metadata for Dagster events.

    .. note:: This class is no longer usable in any Dagster API, and will be completely removed in 2.0.

    Lists of objects of this type can be passed as arguments to Dagster events and will be displayed
    in the Dagster UI and other tooling.

    Should be yielded from within an IO manager to append metadata for a given input/output event.
    For other event types, passing a dict with `MetadataValue` values to the `metadata` argument
    is preferred.

    Args:
        label (str): Short display label for this metadata entry.
        description (Optional[str]): A human-readable description of this metadata entry.
        value (MetadataValue): Typed metadata entry data. The different types allow
            for customized display in tools like the Dagster UI.
    """

    def __new__(
        cls,
        label: str,
        description: Optional[str] = None,
        entry_data: Optional["RawMetadataValue"] = None,
        value: Optional["RawMetadataValue"] = None,
    ):
        value = cast(
            RawMetadataValue,
            normalize_renamed_param(
                new_val=value,
                new_arg="value",
                old_val=entry_data,
                old_arg="entry_data",
            ),
        )
        value = normalize_metadata_value(value)

        return super().__new__(
            cls,
            check.str_param(label, "label"),
            check.opt_str_param(description, "description"),
            check.inst_param(value, "value", MetadataValue),
        )

    @property
    def value(self):
        """Alias of `entry_data`."""
        return self.entry_data
