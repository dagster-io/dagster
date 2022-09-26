from typing import Any, Dict, Tuple

from .types import ManagedStackDiff


def diff_dicts(
    config_dict: Dict[str, Any], dst_dict: Dict[str, Any]
) -> Tuple[bool, ManagedStackDiff]:
    res = True
    diff = ManagedStackDiff()

    for key in set(config_dict.keys()).union(set(dst_dict.keys())):
        if key not in config_dict:
            res = False
            diff = diff.delete(key, dst_dict[key])
        elif key not in dst_dict:
            res = False
            diff = diff.add(key, config_dict[key])
        elif type(config_dict[key]) == dict:
            nested_res, nested_diff = diff_dicts(config_dict[key], dst_dict[key])
            if not nested_res:
                res = False
                diff = diff.with_nested(key, nested_diff)
        elif config_dict[key] != dst_dict[key] and not dst_dict[key] == "**********":
            res = False
            diff = diff.modify(key, dst_dict[key], config_dict[key])
    return (res, diff)
