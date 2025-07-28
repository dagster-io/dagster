from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Optional


class StateStore(ABC):
    """Interface for a state store that can be used to store and retrieve state for a given defs key.

    Also contains a contextually supplied singleton instance of the StateStore, which can be set
    using the `set` class method. This is used to ensure a StateStore is available to code
    that is loading definitions.
    """

    _current: ClassVar[Optional["StateStore"]] = None

    @abstractmethod
    def get_latest_state_version_for_defs(self, defs_key: str) -> Optional[str]:
        """Returns the saved state version for the given defs key, if it exists.

        Args:
            defs_key (str): The key of the defs to retrieve the state for.

        Returns:
            Optional[str]: The saved state version for the given defs key, if it exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def load_state_file(self, defs_key: str, version: str, file_path: Path) -> bool:
        """Loads the state file for the given defs key and version into the given file path.

        Args:
            defs_key (str): The key of the defs to retrieve the state for.
            version (str): The version of the state to retrieve.
            file_path (Path): The path to write the state to.

        Returns:
            bool: True if the state was loaded, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def persist_state_from_file(self, defs_key: str, version: str, file_path: Path) -> None:
        """Persists the defs state stored at `file_path` to persistent storage.

        Args:
            defs_key (str): The key of the defs to persist the state for.
            version (str): The version of the state to persist.
            file_path (Path): The path to the state to persist.
        """
        raise NotImplementedError()

    @classmethod
    def set_current(cls, state_store: "StateStore") -> None:
        """Set the current StateStore."""
        cls._current = state_store

    @classmethod
    def get_current(cls) -> Optional["StateStore"]:
        """Get the current StateStore, if it has been set."""
        from dagster._core.instance import DagsterInstance
        from dagster._core.instance.ref import InstanceRef

        if isinstance(cls._current, InstanceRef):
            return DagsterInstance.from_ref(cls._current)
        return cls._current
