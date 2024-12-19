import shutil
import sys
from pathlib import Path
from typing import Final, Literal, Optional, Tuple

from typing_extensions import Self, TypeAlias

from dagster_dg.config import DgConfig

_CACHE_CONTAINER_DIR_NAME: Final = "dg-cache"

CachableDataType: TypeAlias = Literal["component_registry_data"]


def get_default_cache_dir() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "dg" / "cache"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "dg"
    else:
        return Path.home() / ".cache" / "dg"


class DgCache:
    @classmethod
    def from_default(cls) -> Self:
        return cls.from_parent_path(get_default_cache_dir())

    @classmethod
    def from_config(cls, config: DgConfig) -> Self:
        return cls.from_parent_path(
            parent_path=config.cache_dir,
            logging_enabled=config.verbose,
        )

    # This is the preferred constructor to use when creating a cache. It ensures that all data is
    # stored inside an additional container directory inside the user-specified cache directory.
    # When we clear the cache, we only delete this container directory. This is to avoid accidents
    # when the user mistakenly specifies a cache directory that contains other data.
    @classmethod
    def from_parent_path(cls, parent_path: Path, logging_enabled: bool = False) -> Self:
        root_path = parent_path / _CACHE_CONTAINER_DIR_NAME
        return cls(root_path, logging_enabled)

    def __init__(self, root_path: Path, logging_enabled: bool):
        self._root_path = root_path
        self._root_path.mkdir(parents=True, exist_ok=True)
        self._logging_enabled = logging_enabled

    def clear_key(self, key: Tuple[str, ...]) -> None:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            self.log(f"CACHE [clear-key]: {path}")

    def clear_all(self) -> None:
        shutil.rmtree(self._root_path)
        self.log(f"CACHE [clear-all]: {self._root_path}")

    def get(self, key: Tuple[str, ...]) -> Optional[str]:
        path = self._get_path(key)
        if path.exists():
            self.log(f"CACHE [hit]: {path}")
            return path.read_text()
        else:
            self.log(f"CACHE [miss]: {path}")
            return None

    def set(self, key: Tuple[str, ...], value: str) -> None:
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        self.log(f"CACHE [write]: {path}")

    def _get_path(self, key: Tuple[str, ...]) -> Path:
        return Path(self._root_path, *key)

    def log(self, message: str) -> None:
        if self._logging_enabled:
            print(message)  # noqa: T201
