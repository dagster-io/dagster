from __future__ import annotations

from typing_extensions import Final

from dagster import _check as check


class LogicalVersion:
    """Class that represents a logical version for an asset.

    Args:
        value (str): An arbitrary string representing a logical version.
    """

    def __init__(self, value: str):
        self.value = check.str_param(value, "value")

    def __eq__(self, other: LogicalVersion):
        return self.value == other.value


DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")
