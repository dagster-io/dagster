from collections.abc import Mapping
from typing import Any, Callable, Optional

from dagster_managed_elements.types import ManagedElementDiff

UNSET = object()


def diff_dicts(
    config_dict: Optional[Mapping[str, Any]],
    dst_dict: Optional[Mapping[str, Any]],
    custom_compare_fn: Optional[Callable[[str, Any, Any], Optional[bool]]] = None,
) -> ManagedElementDiff:
    """Utility function which builds a ManagedElementDiff given two dictionaries.

    Args:
        config_dict (Optional[Dict[str, Any]]): The dictionary from the user config.
        dst_dict (Optional[Dict[str, Any]]): The dictionary from the destination.
        custom_compare_fn (Optional[Callable[[Any, Any], bool]]): A custom comparison function to
            use for comparing values in the dictionaries. Passed both values, either of which might be
            the sentinel "UNSET" value. Return True if the two values are the same.
            Return False if the two values are different. Return None if the function should not
            handle the comparison.
    """
    diff = ManagedElementDiff()

    config_dict = config_dict or {}
    dst_dict = dst_dict or {}

    for key in set(config_dict.keys()).union(set(dst_dict.keys())):
        # Both dicts have the key with a dict value - recurse and
        # compare the nested dicts
        if type(config_dict.get(key)) == dict and type(dst_dict.get(key)) == dict:
            nested_diff = diff_dicts(config_dict[key], dst_dict[key], custom_compare_fn)
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        # If one dict has the key as a dict but not the other,
        # recurse and optionally remove the non-dict value in the other
        elif type(config_dict.get(key)) == dict:
            if key in dst_dict:
                diff = diff.delete(key, dst_dict[key])
            nested_diff = diff_dicts(config_dict[key], {}, custom_compare_fn)
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        elif type(dst_dict.get(key)) == dict:
            if key in config_dict:
                diff = diff.add(key, config_dict[key])
            nested_diff = diff_dicts({}, dst_dict[key], custom_compare_fn)
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        # Handle non-dict values
        else:
            custom_compare_result = (
                custom_compare_fn(key, config_dict.get(key, UNSET), dst_dict.get(key, UNSET))
                if custom_compare_fn
                else None
            )
            if custom_compare_result is False:
                if key not in config_dict:
                    diff = diff.delete(key, dst_dict[key])
                elif key not in dst_dict:
                    diff = diff.add(key, config_dict[key])
                else:
                    diff = diff.modify(key, dst_dict[key], config_dict[key])
            elif custom_compare_result is True:
                pass
            else:
                if key not in config_dict:
                    diff = diff.delete(key, dst_dict[key])
                elif key not in dst_dict:
                    diff = diff.add(key, config_dict[key])
                elif config_dict[key] != dst_dict[key]:
                    diff = diff.modify(key, dst_dict[key], config_dict[key])
    return diff
