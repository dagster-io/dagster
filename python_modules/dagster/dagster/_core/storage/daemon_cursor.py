from abc import abstractmethod
from collections.abc import Mapping


class DaemonCursorStorage:
    @abstractmethod
    def get_cursor_values(self, keys: set[str]) -> Mapping[str, str]:
        """Retrieve the value for a given key in the current deployment."""

    @abstractmethod
    def set_cursor_values(self, pairs: Mapping[str, str]) -> None:
        """Set the value for a given key in the current deployment."""
