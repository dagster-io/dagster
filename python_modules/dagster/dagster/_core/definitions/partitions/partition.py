from typing import Any, Generic, Optional

from typing_extensions import TypeVar

import dagster._check as check
from dagster._annotations import deprecated

T_cov = TypeVar("T_cov", default=Any, covariant=True)


@deprecated(breaking_version="2.0", additional_warn_text="Use string partition keys instead.")
class Partition(Generic[T_cov]):
    """A Partition represents a single slice of the entire set of a job's possible work. It consists
    of a value, which is an object that represents that partition, and an optional name, which is
    used to label the partition in a human-readable way.

    Args:
        value (Any): The object for this partition
        name (str): Name for this partition
    """

    def __init__(self, value: Any, name: Optional[str] = None):
        self._value = value
        self._name = check.str_param(name or str(value), "name")

    @property
    def value(self) -> T_cov:
        return self._value

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Partition):
            return False
        else:
            return self.value == other.value and self.name == other.name
