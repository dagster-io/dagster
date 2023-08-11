import json
from typing import Any, Optional, Sequence, TypeVar

from dagster_external.protocol import ExternalExecutionContextData, ExternalExecutionExtras

T = TypeVar("T")


class DagsterExternalError(Exception):
    pass


def assert_not_none(value: Optional[T], desc: Optional[str] = None) -> T:
    if value is None:
        raise DagsterExternalError(f"Missing required property: {desc}")
    return value


def assert_defined_asset_property(value: Optional[T], key: str) -> T:
    return assert_not_none(value, f"`{key}` is undefined. Current step does not target an asset.")


# This should only be called under the precondition that the current steps targets assets.
def assert_single_asset(data: ExternalExecutionContextData, key: str) -> None:
    asset_keys = data["asset_keys"]
    assert asset_keys is not None
    if len(asset_keys) != 1:
        raise DagsterExternalError(f"`{key}` is undefined. Current step targets multiple assets.")


def assert_defined_partition_property(value: Optional[T], key: str) -> T:
    return assert_not_none(
        value, f"`{key}` is undefined. Current step does not target any partitions."
    )


# This should only be called under the precondition that the current steps targets assets.
def assert_single_partition(data: ExternalExecutionContextData, key: str) -> None:
    partition_key_range = data["partition_key_range"]
    assert partition_key_range is not None
    if partition_key_range["start"] != partition_key_range["end"]:
        raise DagsterExternalError(
            f"`{key}` is undefined. Current step targets multiple partitions."
        )


def assert_defined_extra(extras: ExternalExecutionExtras, key: str) -> Any:
    if key not in extras:
        raise DagsterExternalError(f"Extra `{key}` is undefined. Extras must be provided by user.")
    return extras[key]


def assert_param_type(value: T, expected_type: Any, method: str, param: str) -> T:
    if not isinstance(value, expected_type):
        raise DagsterExternalError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected `{expected_type}`, got"
            f" `{type(value)}`."
        )
    return value


def assert_param_value(value: T, expected_values: Sequence[T], method: str, param: str) -> T:
    if value not in expected_values:
        raise DagsterExternalError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def assert_param_json_serializable(value: T, method: str, param: str) -> T:
    try:
        json.dumps(value)
    except (TypeError, OverflowError):
        raise DagsterExternalError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected a JSON-serializable"
            f" type, got `{type(value)}`."
        )
    return value
