from collections.abc import Hashable, Mapping, Sequence, Set
from typing import Any, NamedTuple, Union, overload

from pydantic import BaseModel


def hash_collection(
    collection: Union[Mapping[Hashable, Any], Sequence[Any], Set[Any], tuple[Any, ...], NamedTuple],
) -> int:
    """Hash a mutable collection or immutable collection containing mutable elements.

    This is useful for hashing Dagster-specific NamedTuples that contain mutable lists or dicts.
    The default NamedTuple __hash__ function assumes the contents of the NamedTuple are themselves
    hashable, and will throw an error if they are not. This can occur when trying to e.g. compute a
    cache key for the tuple for use with `lru_cache`.

    This alternative implementation will recursively process collection elements to convert basic
    lists and dicts to tuples prior to hashing. It is recommended to cache the result:

    Example:
        .. code-block:: python

            def __hash__(self):
                if not hasattr(self, '_hash'):
                    self._hash = hash_named_tuple(self)
                return self._hash
    """
    assert isinstance(
        collection, (list, dict, set, tuple)
    ), f"Cannot hash collection of type {type(collection)}"
    return hash(make_hashable(collection))


@overload
def make_hashable(value: Union[list[Any], set[Any]]) -> tuple[Any, ...]: ...


@overload
def make_hashable(value: dict[Any, Any]) -> tuple[tuple[Any, Any]]: ...


@overload
def make_hashable(value: Any) -> Any: ...


def make_hashable(value: Any) -> Any:
    from dagster_shared.record import as_dict, is_record

    if isinstance(value, dict):
        return tuple(sorted((key, make_hashable(val)) for key, val in value.items()))
    elif is_record(value):
        return tuple(make_hashable(val) for val in as_dict(value).values())
    elif isinstance(value, (list, tuple, set)):
        return tuple([make_hashable(x) for x in value])
    elif isinstance(value, BaseModel):
        return make_hashable(value.dict())
    else:
        return value
