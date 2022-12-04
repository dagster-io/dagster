import os
import random
import string
import uuid
import warnings
from collections import OrderedDict
from typing import Tuple, Union, cast

import toposort as toposort_

import dagster._check as check
from dagster._utils import frozendict, library_version_from_core_version, parse_package_version

BACKFILL_TAG_LENGTH = 8

PYTHON_LOGGING_LEVELS_MAPPING = frozendict(
    OrderedDict({"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10})
)

PYTHON_LOGGING_LEVELS_ALIASES = frozendict(OrderedDict({"FATAL": "CRITICAL", "WARN": "WARNING"}))

PYTHON_LOGGING_LEVELS_NAMES = frozenset(
    [
        level_name.lower()
        for level_name in sorted(
            list(PYTHON_LOGGING_LEVELS_MAPPING.keys()) + list(PYTHON_LOGGING_LEVELS_ALIASES.keys())
        )
    ]
)


def coerce_valid_log_level(log_level: Union[str, int]) -> int:
    """Convert a log level into an integer for consumption by the low-level Python logging API."""
    if isinstance(log_level, int):
        return log_level
    check.str_param(log_level, "log_level")
    check.invariant(
        log_level.lower() in PYTHON_LOGGING_LEVELS_NAMES,
        "Bad value for log level {level}: permissible values are {levels}.".format(
            level=log_level,
            levels=", ".join(
                ["'{}'".format(level_name.upper()) for level_name in PYTHON_LOGGING_LEVELS_NAMES]
            ),
        ),
    )
    log_level = PYTHON_LOGGING_LEVELS_ALIASES.get(log_level.upper(), log_level.upper())
    return PYTHON_LOGGING_LEVELS_MAPPING[log_level]


def toposort(data):
    # Workaround a bug in older versions of toposort that choke on frozenset
    data = {k: set(v) if isinstance(v, frozenset) else v for k, v in data.items()}
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]


def make_new_run_id() -> str:
    return str(uuid.uuid4())


def make_new_backfill_id():
    return "".join(random.choice(string.ascii_lowercase) for x in range(BACKFILL_TAG_LENGTH))


def str_format_list(items):
    return "[{items}]".format(items=", ".join(["'{item}'".format(item=item) for item in items]))


def str_format_set(items):
    return "[{items}]".format(items=", ".join(["'{item}'".format(item=item) for item in items]))


def check_dagster_package_version(library_name: str, library_version: str) -> None:
    # This import must be internal in order for this function to be testable
    from dagster.version import __version__

    parsed_lib_version = parse_package_version(library_version)
    if parsed_lib_version.release[0] >= 1:
        if library_version != __version__:
            message = (
                f"Found version mismatch between `dagster` ({__version__})"
                f"and `{library_name}` ({library_version})"
            )
            warnings.warn(message)
    else:
        target_version = library_version_from_core_version(__version__)
        if library_version != target_version:
            message = (
                f"Found version mismatch between `dagster` ({__version__}) "
                f"expected library version ({target_version} "
                f"and `{library_name}` ({library_version})."
            )
            warnings.warn(message)


def parse_env_var(env_var_str: str) -> Tuple[str, str]:
    if "=" in env_var_str:
        split = env_var_str.split("=", maxsplit=1)
        return (split[0], split[1])
    else:
        env_var_value = os.getenv(env_var_str)
        if env_var_value is None:
            raise Exception(f"Tried to load environment variable {env_var_str}, but it was not set")
        return (env_var_str, cast(str, env_var_value))
