import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional, cast

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance

if TYPE_CHECKING:
    from dagster._core.storage.runs.base import RunStorage


class StateStorage(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Interface for a state store that can be used to store and retrieve state for a given defs key.

    Also contains a contextually supplied singleton instance of the StateStore, which can be set
    using the `set` class method. This is used to ensure a StateStore is available to code
    that is loading definitions.
    """

    _current: ClassVar[Optional["StateStorage"]] = None

    @staticmethod
    def from_run_storage(run_storage: "RunStorage") -> "RunStorageStateStorage":
        return RunStorageStateStorage(run_storage)

    def get_latest_version(self, key: str) -> Optional[str]:
        """Returns the saved state version for the given defs key, if it exists.

        Args:
            key (str): The key of the state to retrieve.

        Returns:
            Optional[str]: The saved state version for the given key, if it exists.
        """
        return self.get_latest_versions().get(key)

    @abstractmethod
    def get_latest_versions(self) -> Mapping[str, str]:
        """Returns the saved state version for all defs keys.

        Returns:
            Mapping[str, str]: A mapping of defs key to saved state version.
        """
        raise NotImplementedError()

    @abstractmethod
    def load_state_to_path(self, key: str, version: str, path: Path) -> None:
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
    def store_state(self, key: str, version: str, path: Path) -> None:
        """Persists the state stored at `path` to persistent storage.

        Args:
            key (str): The key of the state to persist.
            version (str): The version of the state to persist.
            file_path (Path): The path to the state to persist.
        """
        raise NotImplementedError()

    def _get_version_key(self, key: str) -> str:
        """Returns a storage key under which the latest version of a given key's state is stored."""
        return f"__version__/{key}"

    def _get_state_key(self, key: str, version: str) -> str:
        """Returns a storage key under which a given key's state at a given version is stored."""
        return f"__state__/{key}/{version}"

    @classmethod
    def set_current(cls, state_storage: "StateStorage") -> None:
        """Set the current StateStorage."""
        cls._current = state_storage

    @classmethod
    def get_current(cls) -> Optional["StateStorage"]:
        """Get the current StateStorage, if it has been set."""
        from dagster._core.instance import DagsterInstance
        from dagster._core.instance.ref import InstanceRef

        if isinstance(cls._current, InstanceRef):
            return DagsterInstance.from_ref(cls._current).state_storage
        return cls._current


class RunStorageStateStorage(StateStorage):
    """Implements StateStorage using a RunStorage as the backing store."""

    VERSIONS_KEY = "__latest_state_versions__"

    def __init__(self, run_storage: "RunStorage"):
        self._run_storage = run_storage
        print("TYPE", type(self._run_storage))

    def get_latest_version(self, key: str) -> Optional[str]:
        cursor_values_res = self._run_storage.get_cursor_values({self._get_version_key(key)})
        print("CURSOR VALUES RES", cursor_values_res)
        return cursor_values_res.get(self._get_version_key(key))

    def get_latest_versions(self) -> Mapping[str, str]:
        return cast(
            "Mapping[str, str]",
            json.loads(
                self._run_storage.get_cursor_values({self.VERSIONS_KEY}).get(
                    self.VERSIONS_KEY, "{}"
                )
            ),
        )

    def load_state_to_path(self, key: str, version: str, path: Path) -> None:
        state_key = self._get_state_key(key, version)
        state_value = self._run_storage.get_cursor_values({state_key}).get(state_key)
        if state_value:
            path.write_bytes(state_value.encode("utf-8"))
            return
        raise ValueError(f"No state found for key {key} and version {version}")

    def _update_latest_version(self, key: str, version: str) -> None:
        current_versions = self.get_latest_versions()
        self._run_storage.set_cursor_values(
            {self.VERSIONS_KEY: json.dumps({**current_versions, key: version})}
        )

    def store_state(self, key: str, version: str, path: Path) -> None:
        state_key = self._get_state_key(key, version)
        self._run_storage.set_cursor_values({state_key: path.read_bytes().decode("utf-8")})
        self._update_latest_version(key, version)
