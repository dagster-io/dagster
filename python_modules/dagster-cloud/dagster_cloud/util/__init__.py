import zlib
from collections import namedtuple
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from io import BytesIO
from typing import Any

from dagster import (
    Field,
    _check as check,
)
from dagster._config import BoolSourceType, IntSourceType, StringSourceType
from dagster._serdes import serialize_value
from dagster_shared.serdes.serdes import PackableValue


class SerializableNamedtupleMapDiff(
    namedtuple(
        "_SerializableNamedtupleMapDiff",
        "to_add to_update to_remove",
    )
):
    def __new__(
        cls,
        to_add,
        to_update,
        to_remove,
    ):
        return super().__new__(
            cls,
            check.set_param(to_add, "to_add", tuple),
            check.set_param(to_update, "to_update", tuple),
            check.set_param(to_remove, "to_remove", tuple),
        )


def diff_serializable_namedtuple_map(desired_map, actual_map, update_key_fn: Callable):
    desired_keys = set(desired_map.keys())
    actual_keys = set(actual_map.keys())

    to_add = desired_keys.difference(actual_keys)
    to_remove = actual_keys.difference(desired_keys)

    existing = actual_keys.intersection(desired_keys)

    to_update = {
        existing_key
        for existing_key in existing
        if update_key_fn(desired_map[existing_key]) != update_key_fn(actual_map[existing_key])
    }

    return SerializableNamedtupleMapDiff(to_add, to_update, to_remove)


def get_env_names_from_config(
    config_schema: dict[str, Field], config_dict: dict[str, Any]
) -> list[str]:
    env_vars = []
    for field_name, field in config_schema.items():
        config_type = field.config_type
        if isinstance(
            config_type, (StringSourceType, IntSourceType, BoolSourceType)
        ) and isinstance(config_dict.get(field_name), dict):
            env_name = config_dict[field_name].get("env")
            if env_name:
                env_vars.append(env_name)

    return env_vars


NON_ISOLATED_RUN_TAG_PAIR = ("dagster/isolation", "disabled")


def is_isolated_run(run):
    return run.tags.get(NON_ISOLATED_RUN_TAG_PAIR[0]) != NON_ISOLATED_RUN_TAG_PAIR[1]


SERVER_HANDLE_TAG = ".dagster/server_handle"


def keys_not_none(
    keys: list[str],
    dictionary: Mapping[str, Any],
) -> bool:
    return all(key in dictionary and dictionary[key] is not None for key in keys)


@contextmanager
def compressed_namedtuple_upload_file(to_serialize: PackableValue):
    compressed_data = zlib.compress(serialize_value(to_serialize).encode("utf-8"))
    with BytesIO(compressed_data) as f:
        yield f
