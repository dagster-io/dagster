import copy
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

import dagster._check as check

K = TypeVar("K")
V = TypeVar("V")
K2 = TypeVar("K2")
V2 = TypeVar("V2")


def _deep_merge_dicts(
    onto_dict: dict[K, V], from_dict: Mapping[K2, V2]
) -> dict[Union[K, K2], Union[V, V2, dict[object, object]]]:
    check.mapping_param(from_dict, "from_dict")
    check.dict_param(onto_dict, "onto_dict")

    _onto_dict = cast(dict[Union[K, K2], Union[V, V2, dict[object, object]]], onto_dict)
    for from_key, from_value in from_dict.items():
        if from_key not in onto_dict:
            _onto_dict[from_key] = from_value
        else:
            onto_value = _onto_dict[from_key]

            if isinstance(from_value, dict) and isinstance(onto_value, dict):
                _onto_dict[from_key] = _deep_merge_dicts(onto_value, from_value)
            else:
                _onto_dict[from_key] = from_value  # smash

    return _onto_dict


def deep_merge_dicts(
    onto_dict: Mapping[K, V], from_dict: Mapping[K2, V2]
) -> dict[Union[K, K2], Union[V, V2, dict[object, object]]]:
    """Returns a recursive union of two input dictionaries:
    * The returned dictionary has an entry for any key that's in either of the inputs.
    * For any key whose value is a dictionary in both of the inputs, the returned value will
      be the result of deep-merging the two input sub-dictionaries.

    If from_dict and onto_dict have different values for the same key, and the values are not both
    dictionaries, the returned dictionary contains the value from from_dict.
    """
    onto_dict = copy.deepcopy(onto_dict if isinstance(onto_dict, dict) else dict(onto_dict))
    return _deep_merge_dicts(onto_dict, from_dict)


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
