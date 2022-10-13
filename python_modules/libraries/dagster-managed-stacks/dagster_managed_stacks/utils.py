from typing import Any, Dict

from .types import ManagedStackDiff


def diff_dicts(
    config_dict: Dict[str, Any],
    dst_dict: Dict[str, Any],
) -> ManagedStackDiff:
    """
    Utility function which builds a ManagedStackDiff given two dictionaries.
    """
    diff = ManagedStackDiff()

    for key in set(config_dict.keys()).union(set(dst_dict.keys())):
        if key not in config_dict:
            diff = diff.delete(key, dst_dict[key])
        elif key not in dst_dict:
            diff = diff.add(key, config_dict[key])
        elif type(config_dict[key]) == dict:
            nested_diff = diff_dicts(config_dict[key], dst_dict[key])
            if not nested_diff.is_empty():
                diff = diff.with_nested(key, nested_diff)
        elif config_dict[key] != dst_dict[key]:
            diff = diff.modify(key, dst_dict[key], config_dict[key])
    return diff
