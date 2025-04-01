import copy
from collections.abc import Mapping
from typing import TypeVar, Union, cast

import dagster_shared.check as check

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
