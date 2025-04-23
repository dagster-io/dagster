import logging
import shutil
from pathlib import Path
from typing import Final, Literal, Optional

from dagster_shared.serdes.errors import DeserializationError
from dagster_shared.serdes.serdes import PackableValue, deserialize_value
from typing_extensions import Self, TypeAlias, TypeVar

from dagster_dg.config import DgConfig
from dagster_dg.utils import get_logger, is_macos, is_windows

_CACHE_CONTAINER_DIR_NAME: Final = "dg-cache"

CachableDataType: TypeAlias = Literal[
    "plugin_registry_data", "all_components_schema", "dg_update_check_timestamp"
]

T_PackableValue = TypeVar("T_PackableValue", bound=PackableValue, default=PackableValue)


def get_default_cache_dir() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "dg" / "cache"
    elif is_macos():
        return Path.home() / "Library" / "Caches" / "dg"
    else:
        return Path.home() / ".cache" / "dg"


class DgCache:
    @classmethod
    def from_default(cls) -> Self:
        return cls.from_parent_path(get_default_cache_dir(), get_logger("dagster_dg.cache", False))

    @classmethod
    def from_config(cls, config: DgConfig) -> Self:
        return cls.from_parent_path(
            parent_path=config.cli.cache_dir,
            log=get_logger("dagster_dg.cache", config.cli.verbose),
        )

    # This is the preferred constructor to use when creating a cache. It ensures that all data is
    # stored inside an additional container directory inside the user-specified cache directory.
    # When we clear the cache, we only delete this container directory. This is to avoid accidents
    # when the user mistakenly specifies a cache directory that contains other data.
    @classmethod
    def from_parent_path(cls, parent_path: Path, log: logging.Logger) -> Self:
        root_path = parent_path / _CACHE_CONTAINER_DIR_NAME
        return cls(root_path, log)

    def __init__(self, root_path: Path, log: logging.Logger) -> None:
        self._root_path = root_path
        self._root_path.mkdir(parents=True, exist_ok=True)
        self.log = log

    def clear_key(self, key: tuple[str, ...]) -> None:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            self.log.info(f"CACHE [clear-key]: {path}")

    def clear_all(self) -> None:
        shutil.rmtree(self._root_path)
        self.log.info(f"CACHE [clear-all]: {self._root_path}")

    def get(self, key: tuple[str, ...], type_: type[T_PackableValue]) -> Optional[T_PackableValue]:
        path = self._get_path(key)
        if path.exists():
            self.log.info(f"CACHE [hit]: {path}")
            raw_data = path.read_text()

            # If we encounter a deserialization error (which can happen due to version skew),
            # just treat the cache as invalid and return None so data will be refetched.
            try:
                return deserialize_value(raw_data, as_type=type_)
            except DeserializationError as e:
                self.log.info(f"CACHE [deserialization-error]: {path} - {e}")
                return None
        else:
            self.log.info(f"CACHE [miss]: {path}")
            return None

    def set(self, key: tuple[str, ...], value: str) -> None:
        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        self.log.info(f"CACHE [write]: {path}")

    def _get_path(self, key: tuple[str, ...]) -> Path:
        return Path(self._root_path, *key)
