from abc import ABC, abstractmethod
from functools import lru_cache
from typing import AbstractSet, Any, Mapping, Type

from typing_extensions import TypeVar

from dagster import _check as check
from dagster._model import DagsterModel
from dagster._model.pydantic_compat_layer import model_fields
from dagster._utils.typing_api import flatten_unions

T_NamespacedTagSet = TypeVar("T_NamespacedTagSet", bound="NamespacedTagSet")


class NamespacedTagSet(ABC, DagsterModel):
    """Extend this class to define a set of tags fields in the same namespace.

    Supports splatting to a dictionary that can be placed inside a tags argument along with
    other tags.

    .. code-block:: python

        my_tags: NamespacedTagsSet = ...
        @asset(
            tags={**my_tags}
        )
        def my_asset():
            pass
    """

    def __init__(self, *args, **kwargs) -> None:
        for field_name in model_fields(self).keys():
            annotation_types = self._get_accepted_types_for_field(field_name)
            invalid_annotation_types = {
                annotation_type
                for annotation_type in annotation_types
                if annotation_type not in (str, type(None))
            }
            if invalid_annotation_types:
                check.failed(
                    f"Type annotation for field '{field_name}' is not str or Optional[str]"
                )
        super().__init__(*args, **kwargs)

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
    def extract(cls: Type[T_NamespacedTagSet], tags: Mapping[str, str]) -> T_NamespacedTagSet:
        """Extracts entries from the provided tags dictionary into an instance of this class.

        Ignores any entries in the tags dictionary whose keys don't correspond to fields on this
        class.

        In general, the following should always pass:

        .. code-block:: python

            class MyTagSet(NamespacedTagSet):
                ...

            tags: MyTagSet  = ...
            assert MyTagSet.extract(dict(metadata)) == metadata

        Args:
            tags (Mapping[str, str]): A dictionary of tags.
        """
        kwargs = {}
        for namespaced_key, value in tags.items():
            splits = namespaced_key.split("/")
            if len(splits) == 2:
                namespace, key = splits
                if namespace == cls.namespace() and key in model_fields(cls):
                    kwargs[key] = value

        return cls(**kwargs)

    @classmethod
    @lru_cache(maxsize=None)  # this avoids wastefully recomputing this once per instance
    def _get_accepted_types_for_field(cls, field_name: str) -> AbstractSet[Type]:
        annotation = model_fields(cls)[field_name].annotation
        return flatten_unions(annotation)
