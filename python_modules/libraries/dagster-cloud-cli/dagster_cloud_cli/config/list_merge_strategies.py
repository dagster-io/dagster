from typing import Any, Callable

from dagster_shared import check
from dagster_shared.utils.hash import hash_collection

ListMergeFunction = Callable[[list[Any], list[Any]], list[Any]]


def replace(from_list: list[Any], _: list[Any]) -> list[Any]:
    return from_list


def append(from_list: list[Any], onto_list: list[Any]) -> list[Any]:
    return onto_list + from_list


def deduplicate(from_list: list[Any], onto_list: list[Any]) -> list[Any]:
    return _deduplicate_list(onto_list + from_list)


def get_list_merger_for_key_value_separated_strings(separator: str) -> ListMergeFunction:
    def func(from_list: list[Any], onto_list: list[Any]) -> list[Any]:
        fl = check.list_param(from_list, "from_list", of_type=str)
        ol = check.list_param(onto_list, "onto_list", of_type=str)
        return _merge_key_value_separated_strings(fl, ol, separator)

    return func


def get_list_merger_for_identifiable_dicts(name_key: str) -> ListMergeFunction:
    def func(from_list: list[Any], onto_list: list[Any]) -> list[Any]:
        fl = check.list_param(from_list, "from_list", of_type=dict)
        ol = check.list_param(onto_list, "onto_list", of_type=dict)
        return _merge_object_list_by_identity(name_key, fl, ol)

    return func


def _deduplicate_list(lst: list[Any]) -> list[Any]:
    result = []
    hashes = set()
    for value in lst:
        value_hash = hash_collection(value) if isinstance(value, (list, dict)) else hash(value)
        if value_hash not in hashes:
            hashes.add(value_hash)
            result.append(value)
    return result


def _merge_key_value_separated_strings(
    from_list: list[str], onto_list: list[str], separator: str
) -> list[str]:
    from_items = [item.split(separator)[0] for item in from_list]
    original_items = []

    for item in onto_list:
        parts = item.split(separator)
        if len(parts) > 2:
            raise ValueError(f"Invalid key-value pair: {item}")

        if parts[0] not in from_items:
            original_items.append(item)

    return original_items + from_list


def _merge_object_list_by_identity(
    name_key: str, from_list: list[dict[str, Any]], onto_list: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    onto_items = {item[name_key]: item for item in onto_list}
    from_items = {item[name_key]: item for item in from_list}

    merged_items = {
        key: item for key, item in onto_items.items() if key not in from_items
    } | from_items
    return list(merged_items.values())
