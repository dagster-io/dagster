import base64
import json
import os
import warnings
import zlib
from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, TypeVar

from ._protocol import (
    ENV_KEY_PREFIX,
    ExtContextData,
    ExtExtras,
    ExtParams,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

T = TypeVar("T")


class DagsterExtError(Exception):
    pass


class DagsterExtWarning(Warning):
    pass


def assert_not_none(value: Optional[T], desc: Optional[str] = None) -> T:
    if value is None:
        raise DagsterExtError(f"Missing required property: {desc}")
    return value


def assert_defined_asset_property(value: Optional[T], key: str) -> T:
    return assert_not_none(value, f"`{key}` is undefined. Current step does not target an asset.")


# This should only be called under the precondition that the current step targets assets.
def assert_single_asset(data: ExtContextData, key: str) -> None:
    asset_keys = data["asset_keys"]
    assert asset_keys is not None
    if len(asset_keys) != 1:
        raise DagsterExtError(f"`{key}` is undefined. Current step targets multiple assets.")


def resolve_optionally_passed_asset_key(
    data: ExtContextData, asset_key: Optional[str], method: str
) -> str:
    asset_keys = assert_defined_asset_property(data["asset_keys"], method)
    asset_key = assert_opt_param_type(asset_key, str, method, "asset_key")
    if asset_key and asset_key not in asset_keys:
        raise DagsterExtError(
            f"Invalid asset key. Expected one of `{asset_keys}`, got `{asset_key}`."
        )
    if not asset_key:
        if len(asset_keys) != 1:
            raise DagsterExtError(
                f"Calling `{method}` without passing an asset key is undefined. Current step"
                " targets multiple assets."
            )
        asset_key = asset_keys[0]
    return asset_key


def assert_defined_partition_property(value: Optional[T], key: str) -> T:
    return assert_not_none(
        value, f"`{key}` is undefined. Current step does not target any partitions."
    )


# This should only be called under the precondition that the current steps targets assets.
def assert_single_partition(data: ExtContextData, key: str) -> None:
    partition_key_range = data["partition_key_range"]
    assert partition_key_range is not None
    if partition_key_range["start"] != partition_key_range["end"]:
        raise DagsterExtError(f"`{key}` is undefined. Current step targets multiple partitions.")


def assert_defined_extra(extras: ExtExtras, key: str) -> Any:
    if key not in extras:
        raise DagsterExtError(f"Extra `{key}` is undefined. Extras must be provided by user.")
    return extras[key]


def assert_param_type(value: T, expected_type: Any, method: str, param: str) -> T:
    if not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected `{expected_type}`, got"
            f" `{type(value)}`."
        )
    return value


def assert_opt_param_type(value: T, expected_type: Any, method: str, param: str) -> T:
    if not (isinstance(value, expected_type) or value is None):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected"
            f" `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def assert_env_param_type(env_params: ExtParams, key: str, expected_type: Type[T], cls: Type) -> T:
    value = env_params.get(key)
    if not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `{expected_type}`, got `{type(value)}`."
        )
    return value


def assert_opt_env_param_type(
    env_params: ExtParams, key: str, expected_type: Type[T], cls: Type
) -> Optional[T]:
    value = env_params.get(key)
    if value is not None and not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def assert_param_value(value: T, expected_values: Sequence[T], method: str, param: str) -> T:
    if value not in expected_values:
        raise DagsterExtError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def assert_param_json_serializable(value: T, method: str, param: str) -> T:
    try:
        json.dumps(value)
    except (TypeError, OverflowError):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected a JSON-serializable"
            f" type, got `{type(value)}`."
        )
    return value


def param_from_env_var(key: str) -> Any:
    raw_value = os.environ.get(param_name_to_env_var(key))
    return decode_env_var(raw_value) if raw_value is not None else None


def encode_env_var(value: Any) -> str:
    serialized = json.dumps(value)
    compressed = zlib.compress(serialized.encode("utf-8"))
    encoded = base64.b64encode(compressed)
    return encoded.decode("utf-8")  # as string


def decode_env_var(value: Any) -> str:
    decoded = base64.b64decode(value)
    decompressed = zlib.decompress(decoded)
    return json.loads(decompressed.decode("utf-8"))


def param_name_to_env_var(param_name: str) -> str:
    return f"{ENV_KEY_PREFIX}{param_name.upper()}"


def env_var_to_param_name(env_var: str) -> str:
    return env_var[len(ENV_KEY_PREFIX) :].lower()


def is_dagster_orchestration_active() -> bool:
    return param_from_env_var("is_orchestration_active")


def emit_orchestration_inactive_warning() -> None:
    warnings.warn(
        "This process was not launched by a Dagster orchestration process. All calls to the"
        " `dagster-ext` context or attempts to initialize `dagster-ext` abstractions"
        " are no-ops.",
        category=DagsterExtWarning,
    )


def get_mock() -> "MagicMock":
    from unittest.mock import MagicMock

    return MagicMock()
