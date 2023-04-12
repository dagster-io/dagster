from abc import abstractmethod
from typing import Mapping, Set


class DaemonCursorStorage:
    @abstractmethod
    def kvs_get(self, keys: Set[str]) -> Mapping[str, str]:
        """Retrieve the value for a given key in the current deployment."""

    @abstractmethod
    def kvs_set(self, pairs: Mapping[str, str]) -> None:
        """Set the value for a given key in the current deployment."""
