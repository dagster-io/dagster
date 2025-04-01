from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from functools import cache
from typing import AbstractSet, Any, Optional  # noqa: UP035

from dagster_shared.dagster_model import DagsterModel
from dagster_shared.dagster_model.pydantic_compat_layer import model_fields
from typing_extensions import TypeVar

from dagster import _check as check
from dagster._core.definitions.metadata.metadata_value import (
    MetadataValue,
    TableColumn as TableColumn,
    TableColumnConstraints as TableColumnConstraints,
    TableColumnLineage,
    TableSchema,
)
from dagster._utils.typing_api import flatten_unions

# Python types that have a MetadataValue types that directly wraps them
DIRECTLY_WRAPPED_METADATA_TYPES = {
    str,
    float,
    int,
    bool,
    TableSchema,
    TableColumnLineage,
    type(None),
}

T_NamespacedKVSet = TypeVar("T_NamespacedKVSet", bound="NamespacedKVSet")


def is_raw_metadata_type(t: type) -> bool:
    return issubclass(t, MetadataValue) or t in DIRECTLY_WRAPPED_METADATA_TYPES


class NamespacedKVSet(ABC, DagsterModel):
    """Base class for defining a set of key-value pairs in the same namespace.

    Includes shared behavior between NamespacedMetadataSet and NamespacedTagSet.

    """

    @classmethod
    @abstractmethod
    def namespace(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def _namespaced_key(cls, key: str) -> str:
        return f"{cls.namespace()}/{key}"

    @staticmethod
    def _strip_namespace_from_key(key: str) -> str:
        return key.split("/", 1)[1]

    def keys(self) -> Iterable[str]:
        return [
            self._namespaced_key(key)
            for key in model_fields(self.__class__).keys()
            # getattr returns the pydantic property on the subclass
            if getattr(self, key) is not None
        ]

    def __getitem__(self, key: str) -> Any:
        # getattr returns the pydantic property on the subclass
        return getattr(self, self._strip_namespace_from_key(key))

    @classmethod
    def extract(cls: type[T_NamespacedKVSet], values: Mapping[str, Any]) -> T_NamespacedKVSet:
        """Extracts entries from the provided dictionary into an instance of this class.

        Ignores any entries in the dictionary whose keys don't correspond to fields on this
        class.

        In general, the following should always pass:

        .. code-block:: python

            class MyKVSet(NamespacedKVSet):
                ...

            metadata: MyKVSet  = ...
            assert MyKVSet.extract(dict(metadata)) == metadata

        Args:
            values (Mapping[str, Any]): A dictionary of entries to extract.
        """
        kwargs = {}
        for namespaced_key, value in values.items():
            splits = namespaced_key.split("/")
            if len(splits) == 2:
                namespace, key = splits
                if namespace == cls.namespace() and key in model_fields(cls):
                    kwargs[key] = cls._extract_value(field_name=key, value=value)
                elif namespace == cls.namespace() and key in cls.current_key_by_legacy_key():
                    current_key = cls.current_key_by_legacy_key()[key]
                    if f"{cls.namespace()}/{current_key}" not in values:
                        # Only extract the value from the backcompat key if the new
                        # key is not present
                        kwargs[current_key] = cls._extract_value(
                            field_name=current_key, value=value
                        )

        return cls(**kwargs)

    @classmethod
    @abstractmethod
    def _extract_value(cls, field_name: str, value: Any) -> Any:
        """Based on type annotation, potentially coerce the value to the expected type."""
        ...

    @classmethod
    def current_key_by_legacy_key(cls) -> Mapping[str, str]:
        """Return a mapping of each legacy key to its current key."""
        return {}


class NamespacedMetadataSet(NamespacedKVSet):
    """Extend this class to define a set of metadata fields in the same namespace.

    Supports splatting to a dictionary that can be placed inside a metadata argument along with
    other dictionary-structured metadata.

    .. code-block:: python

        my_metadata: NamespacedMetadataSet = ...
        return MaterializeResult(metadata={**my_metadata, ...})
    """

    def __init__(self, *args, **kwargs) -> None:
        for field_name in model_fields(self.__class__).keys():
            annotation_types = self._get_accepted_types_for_field(field_name)
            invalid_annotation_types = {
                annotation_type
                for annotation_type in annotation_types
                if not is_raw_metadata_type(annotation_type)
            }
            if invalid_annotation_types:
                check.failed(
                    f"Type annotation for field '{field_name}' includes invalid metadata type(s): {invalid_annotation_types}"
                )
        super().__init__(*args, **kwargs)

    @classmethod
    def _extract_value(cls, field_name: str, value: Any) -> Any:
        """Based on type annotation, potentially coerce the metadata value to its inner value.

        E.g. if the annotation is Optional[float] and the value is FloatMetadataValue, construct
        the MetadataSet using the inner float.
        """
        if isinstance(value, MetadataValue):
            annotation = model_fields(cls)[field_name].annotation
            annotation_acceptable_types = flatten_unions(annotation)
            if (
                type(value) not in annotation_acceptable_types
                and type(value.value) in annotation_acceptable_types
            ):
                check.invariant(type(value.value) in DIRECTLY_WRAPPED_METADATA_TYPES)
                return value.value

        return value

    @classmethod
    @cache  # this avoids wastefully recomputing this once per instance
    def _get_accepted_types_for_field(cls, field_name: str) -> AbstractSet[type]:
        annotation = model_fields(cls)[field_name].annotation
        return flatten_unions(annotation)


class TableMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to definitions, observations, or materializations of assets that
    are tables.

    Args:
        column_schema (Optional[TableSchema]): The schema of the columns in the table.
        column_lineage (Optional[TableColumnLineage]): The lineage of column inputs to column
            outputs for the table.
        row_count (Optional[int]): The number of rows in the table.
        partition_row_count (Optional[int]): The number of rows in the materialized or observed partition.
        table_name (Optional[str]): A unique identifier for the table/view, typically fully qualified.
            For example, `my_database.my_schema.my_table`.
    """

    column_schema: Optional[TableSchema] = None
    column_lineage: Optional[TableColumnLineage] = None
    row_count: Optional[int] = None
    partition_row_count: Optional[int] = None
    table_name: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"

    @classmethod
    def current_key_by_legacy_key(cls) -> Mapping[str, str]:
        return {"relation_identifier": "table_name"}


class UriMetadataSet(NamespacedMetadataSet):
    """Metadata entry which supplies a URI address for an asset.
    For example, the S3 address of a file or bucket.

    Args:
        uri (Optional[str]): The URI address for the asset.
    """

    uri: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"
