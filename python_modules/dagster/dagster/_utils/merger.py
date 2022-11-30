import copy
from typing import Any, Dict, Mapping, TypeVar, Union, cast

import dagster._check as check

K = TypeVar("K")
V = TypeVar("V")
K2 = TypeVar("K2")
V2 = TypeVar("V2")


def _deep_merge_dicts(
    onto_dict: Dict[K, V], from_dict: Mapping[K2, V2]
) -> Dict[Union[K, K2], Union[V, V2, Dict[object, object]]]:
    check.mapping_param(from_dict, "from_dict")
    check.dict_param(onto_dict, "onto_dict")

    _onto_dict = cast(Dict[Union[K, K2], Union[V, V2, Dict[object, object]]], onto_dict)
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
) -> Dict[Union[K, K2], Union[V, V2, Dict[object, object]]]:
    """
    Returns a recursive union of two input dictionaries:
    * The returned dictionary has an entry for any key that's in either of the inputs.
    * For any key whose value is a dictionary in both of the inputs, the returned value will
      be the result of deep-merging the two input sub-dictionaries.

    If from_dict and onto_dict have different values for the same key, and the values are not both
    dictionaries, the returned dictionary contains the value from from_dict.
    """
    onto_dict = copy.deepcopy(onto_dict if isinstance(onto_dict, dict) else dict(onto_dict))
    return _deep_merge_dicts(onto_dict, from_dict)  # type: ignore # [mypy bug]


def merge_dicts(*args: Mapping[Any, Any]) -> Dict[Any, Any]:
    """
    Returns a dictionary with with all the keys in all of the input dictionaries.

    If multiple input dictionaries have different values for the same key, the returned dictionary
    contains the value from the dictionary that comes latest in the list.
    """
    check.is_tuple(args, of_type=dict)
    if len(args) < 2:
        check.failed(f"Expected 2 or more args to merge_dicts, found {len(args)}")

    result: Dict[object, object] = {}
    for arg in args:
        result.update(arg)
    return result
