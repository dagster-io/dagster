import sys

# pylint: disable=no-name-in-module,unused-import

# see https://stackoverflow.com/questions/53978542/
if sys.version_info[0] >= 3:
    from collections.abc import (
        Callable,
        Container,
        Hashable,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        Mapping,
        MappingView,
        MutableMapping,
        MutableSequence,
        MutableSet,
        Sequence,
        Set,
        Sized,
        ValuesView,
    )
else:
    from collections import (
        Callable,
        Container,
        Hashable,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        Mapping,
        MappingView,
        MutableMapping,
        MutableSequence,
        MutableSet,
        Sequence,
        Set,
        Sized,
        ValuesView,
    )

__all__ = [
    "Callable",
    "Container",
    "Hashable",
    "ItemsView",
    "Iterable",
    "Iterator",
    "KeysView",
    "Mapping",
    "MappingView",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
    "Sized",
    "ValuesView",
]
