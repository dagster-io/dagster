from abc import ABC, abstractmethod
from typing import (
    AbstractSet,
    Any,
    Mapping,
    Optional,
    Type,
)

from typing_extensions import TypeVar

from dagster._model import DagsterModel
from dagster._model.pydantic_compat_layer import model_fields

from .metadata_value import MetadataValue, TableColumnLineage, TableSchema

T_NamespacedMetadataSet = TypeVar("T_NamespacedMetadataSet", bound="NamespacedMetadataSet")


class NamespacedMetadataSet(ABC, DagsterModel):
    """Extend this class to define a set of metadata fields in the same namespace.

    Supports splatting to a dictionary that can be placed inside a metadata argument along with
    other dictionary-structured metadata.

    .. code-block:: python

        my_metadata: NamespacedMetadataSet = ...
        return MaterializeResult(metadata={**my_metadata, ...})
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

    def keys(self) -> AbstractSet[str]:
        return {
            self._namespaced_key(key)
            for key in model_fields(self).keys()
            # getattr returns the pydantic property on the subclass
            if getattr(self, key) is not None
        }

    def __getitem__(self, key: str) -> Any:
        # getattr returns the pydantic property on the subclass
        return getattr(self, self._strip_namespace_from_key(key))

    @classmethod
    def extract(
        cls: Type[T_NamespacedMetadataSet], metadata: Mapping[str, Any]
    ) -> T_NamespacedMetadataSet:
        """Extracts entries from the provided metadata dictionary into an instance of this class.

        Ignores any entries in the metadata dictionary whose keys don't correspond to fields on this
        class.

        In general, the following should always pass:

        .. code-block:: python

            class MyMetadataSet(NamedspacedMetadataSet):
                ...

            metadata: MyMetadataSet  = ...
            assert MyMetadataSet.extract(dict(metadata)) == metadata

        Args:
            metadata (Mapping[str, Any]): A dictionary of metadata entries.
        """
        kwargs = {}
        for namespaced_key, value in metadata.items():
            splits = namespaced_key.split("/")
            if len(splits) == 2:
                namespace, key = splits
                if namespace == cls.namespace() and key in model_fields(cls):
                    kwargs[key] = value.value if isinstance(value, MetadataValue) else value

        return cls(**kwargs)


class TableMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to definitions, observations, or materializations of assets that
    are tables.

    Args:
        column_schema (Optional[TableSchema]): The schema of the columns in the table.
        column_lineage (Optional[TableColumnLineage]): The lineage of column inputs to column
            outputs for the table.
    """

    column_schema: Optional[TableSchema] = None
    column_lineage: Optional[TableColumnLineage] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"
