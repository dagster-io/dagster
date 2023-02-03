import os
import pickle
from typing import Any, Dict

from dagster._utils import mkdir_p
from upath import UPath

PICKLE_PROTOCOL = 4


class NamespaceAwareStorage:
    def __init__(self, storage_root: str, asset_namespace_lookup: Dict[str, str]):
        self.storage_root = storage_root
        self.asset_namespace_lookup = asset_namespace_lookup

    def load_object(self, asset_key: str) -> Any:
        return load_object_from_storage(
            storage_root=self.storage_root,
            namespace=self.asset_namespace_lookup[asset_key],
            file_path=f"{asset_key}.pickle",
        )

    def write_object(self, asset_key, obj: Any):
        return write_object_to_storage(
            storage_root=self.storage_root,
            namespace=self.asset_namespace_lookup[asset_key],
            file_path=f"{asset_key}.pickle",
            obj=obj,
        )


def load_object_from_storage(storage_root: str, namespace: str, file_path: str):
    namespace_folder = os.path.join(storage_root, namespace)
    full_path = os.path.join(namespace_folder, file_path)
    return load_object_from_path(full_path)


def load_object_from_path(path: str):
    print(f"LOADING FROM {path}")
    upath = UPath(path)
    with upath.open("rb") as file:
        return pickle.load(file)


def write_object_to_storage(storage_root: str, namespace: str, file_path: str, obj: Any):
    namespace_folder = os.path.join(storage_root, namespace)
    mkdir_p(namespace_folder)
    full_path = os.path.join(namespace_folder, file_path)
    return write_object_to_path(full_path, obj)


def write_object_to_path(path: str, obj: Any):
    print(f"WRITING TO {path}")
    upath = UPath(path)
    with upath.open("wb") as file:
        pickle.dump(obj, file, PICKLE_PROTOCOL)
