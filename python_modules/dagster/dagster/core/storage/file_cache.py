import io
import os
import shutil
from abc import ABC, abstractmethod

import dagster._check as check
from dagster.config import Field
from dagster.core.definitions import resource
from dagster.utils import mkdir_p

from .file_manager import LocalFileHandle


class FileCache(ABC):
    def __init__(self, overwrite):
        # Overwrite is currently only a signal to callers to not overwrite.
        # These classes currently do not enforce any semantics around that
        self.overwrite = check.bool_param(overwrite, "overwrite")

    @abstractmethod
    def has_file_object(self, file_key):
        pass

    @abstractmethod
    def get_file_handle(self, file_key):
        pass

    @abstractmethod
    def write_file_object(self, file_key, source_file_object):
        pass

    def write_binary_data(self, file_key, binary_data):
        return self.write_file_object(file_key, io.BytesIO(binary_data))


class FSFileCache(FileCache):
    def __init__(self, target_folder, overwrite=False):
        super(FSFileCache, self).__init__(overwrite=overwrite)
        check.str_param(target_folder, "target_folder")
        check.param_invariant(os.path.isdir(target_folder), "target_folder")

        self.target_folder = target_folder

    def has_file_object(self, file_key):
        return os.path.exists(self.get_full_path(file_key))

    def write_file_object(self, file_key, source_file_object):
        target_file = self.get_full_path(file_key)
        with open(target_file, "wb") as dest_file_object:
            shutil.copyfileobj(source_file_object, dest_file_object)
        return LocalFileHandle(target_file)

    def get_file_handle(self, file_key):
        check.str_param(file_key, "file_key")
        return LocalFileHandle(self.get_full_path(file_key))

    def get_full_path(self, file_key):
        check.str_param(file_key, "file_key")
        return os.path.join(self.target_folder, file_key)


@resource(
    {"overwrite": Field(bool, is_required=False, default_value=False), "target_folder": Field(str)}
)
def fs_file_cache(init_context):
    target_folder = init_context.resource_config["target_folder"]

    if not os.path.exists(target_folder):
        mkdir_p(target_folder)

    return FSFileCache(target_folder=target_folder, overwrite=False)
