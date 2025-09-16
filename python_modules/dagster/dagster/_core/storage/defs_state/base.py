from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance

# constant indicating where to store the latest defs state info in a kvs context
DEFS_STATE_INFO_CURSOR_KEY = "__latest_defs_state_info__"

_current_storage: ContextVar[Optional["DefsStateStorage"]] = ContextVar(
    "_current_storage", default=None
)


@contextmanager
def set_defs_state_storage(storage: Optional["DefsStateStorage"]):
    """Context manager to set the current DefsStateStorage, accessible via `DefsStateStorage.get()`."""
    token = _current_storage.set(storage)

    try:
        yield
    finally:
        _current_storage.reset(token)


class DefsStateStorage(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Interface for a state store that can be used to store and retrieve state for a given defs key.

    Also contains a contextually supplied singleton instance of the StateStore, which can be set
    using the `set` class method. This is used to ensure a StateStore is available to code
    that is loading definitions.
    """

    def get_latest_version(self, key: str) -> Optional[str]:
        """Returns the saved state version for the given defs key, if it exists.

        Args:
            key (str): The key of the state to retrieve.

        Returns:
            Optional[str]: The saved state version for the given key, if it exists.
        """
        info = self.get_latest_defs_state_info()
        return info.get_version(key) if info else None

    @abstractmethod
    def get_latest_defs_state_info(self) -> Optional[DefsStateInfo]:
        """Returns the saved state version for all defs keys.

        Returns:
            Optional[DefsStateInfo]: The saved state version info for all defs keys, if available.
        """
        raise NotImplementedError()

    @abstractmethod
    def download_state_to_path(self, key: str, version: str, path: Path) -> None:
        """Loads the state file for the given defs key and version into the given file path.

        Args:
            key (str): The key of the state to retrieve.
            version (str): The version of the state to retrieve.
            path (Path): The path to write the state to.

        Returns:
            bool: True if the state was loaded, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def upload_state_from_path(self, key: str, version: str, path: Path) -> None:
        """Uploads the state stored at `path` to persistent storage.

        Args:
            key (str): The key of the state to persist.
            version (str): The version of the state to persist.
            path (Path): The path to the state to persist.
        """
        raise NotImplementedError()

    @abstractmethod
    def set_latest_version(self, key: str, version: str) -> None:
        """Sets the latest version of the state for the given key.

        Args:
            key (str): The key of the state to persist.
            version (str): The version of the state to persist.
        """
        raise NotImplementedError()

    def _get_version_key(self, key: str) -> str:
        """Returns a storage key under which the latest version of a given key's state is stored."""
        return f"__version__/{key}"

    def _get_state_key(self, key: str, version: str) -> str:
        """Returns a storage key under which a given key's state at a given version is stored."""
        return f"__state__/{key}/{version}"

    @classmethod
    def get(cls) -> Optional["DefsStateStorage"]:
        """Get the current StateStorage, if it has been set."""
        return _current_storage.get()
