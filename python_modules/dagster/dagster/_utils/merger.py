from collections.abc import Mapping
from typing import Any, TypeVar

from dagster_shared.merger import deep_merge_dicts as deep_merge_dicts

import dagster._check as check

K = TypeVar("K")
V = TypeVar("V")
K2 = TypeVar("K2")
V2 = TypeVar("V2")


def merge_dicts(*args: Mapping[Any, Any]) -> dict[Any, Any]:
    """Returns a dictionary with with all the keys in all of the input dictionaries.

    If multiple input dictionaries have different values for the same key, the returned dictionary
    contains the value from the dictionary that comes latest in the list.
    """
    check.is_tuple(args, of_type=dict)
    if len(args) < 2:
        check.failed(f"Expected 2 or more args to merge_dicts, found {len(args)}")

    result: dict[object, object] = {}
    for arg in args:
        result.update(arg)
    return result


def reverse_dict(d: Mapping[V, K]) -> dict[K, V]:
    """Returns a new dictionary with the keys and values of the input dictionary swapped.

    If the input dictionary has duplicate values, the returned dictionary will have the value from
    the last key that maps to it.
    """
    check.dict_param(d, "d")
    return {v: k for k, v in d.items()}
