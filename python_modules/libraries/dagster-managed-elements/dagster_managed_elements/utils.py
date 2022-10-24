from typing import Any, Dict, Optional

from .types import ManagedElementDiff


def diff_dicts(
    config_dict: Optional[Dict[str, Any]],
    dst_dict: Optional[Dict[str, Any]],
) -> ManagedElementDiff:
    """
    Utility function which builds a ManagedElementDiff given two dictionaries.
    """
    diff = ManagedElementDiff()

    config_dict = config_dict or {}
    dst_dict = dst_dict or {}

    for key in set(config_dict.keys()).union(set(dst_dict.keys())):
        # Both dicts have the key with a dict value - recurse and
        # compare the nested dicts
        if type(config_dict.get(key)) == dict and type(dst_dict.get(key)) == dict:
            nested_diff = diff_dicts(config_dict[key], dst_dict[key])
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        # If one dict has the key as a dict but not the other,
        # recurse and optionally remove the non-dict value in the other
        elif type(config_dict.get(key)) == dict:
            if key in dst_dict:
                diff = diff.delete(key, dst_dict[key])
            nested_diff = diff_dicts(config_dict[key], {})
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        elif type(dst_dict.get(key)) == dict:
            if key in config_dict:
                diff = diff.add(key, config_dict[key])
            nested_diff = diff_dicts({}, dst_dict[key])
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        # Handle non-dict values
        elif key not in config_dict:
            diff = diff.delete(key, dst_dict[key])
        elif key not in dst_dict:
            diff = diff.add(key, config_dict[key])
        elif config_dict[key] != dst_dict[key]:
            diff = diff.modify(key, dst_dict[key], config_dict[key])
    return diff
