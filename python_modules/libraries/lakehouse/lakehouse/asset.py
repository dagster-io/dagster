from abc import ABC
from typing import List, Tuple, Union

from dagster import AssetKey, DagsterType, check

from .computation import Computation


class Asset(ABC):
    def __init__(self, storage_key, path, computation):
        self._storage_key = check.str_param(storage_key, "storage_key")
        self._path = canonicalize_path(path)
        self._computation = check.opt_inst_param(computation, "computation", Computation)
        self._dagster_type = DagsterType(type_check_fn=lambda a, b: True, name=".".join(self.path))

    @property
    def storage_key(self):
        return self._storage_key

    @property
    def path(self):
        return self._path

    @property
    def key(self):
        return AssetKey(list(self.path))

    @property
    def computation(self):
        return self._computation

    @property
    def dagster_type(self):
        return self._dagster_type


def source_asset(path, storage_key="default_storage"):
    """A source asset is an asset that's not derived inside the lakehouse.  Other assets
    may depend on it, but it has no dependencies that the lakehouse is aware of.
    """
    return Asset(storage_key=storage_key, path=path, computation=None)


def canonicalize_path(path: Union[Tuple[str, ...], List[str], str]) -> Tuple[str, ...]:
    if isinstance(path, str):
        return (path,)
    elif isinstance(path, tuple):
        check.tuple_param(path, "path", of_type=str)
        return path
    elif isinstance(path, list):
        check.list_param(path, "path", of_type=str)
        return tuple(path)
    else:
        check.failed("path param must be a string, list of strings, or tuple of strings")
