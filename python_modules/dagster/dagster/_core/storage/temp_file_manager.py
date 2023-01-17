import contextlib
import os
import shutil
import tempfile

from dagster._core.definitions.resource_definition import resource


class TempfileManager:
    def __init__(self):
        self.paths = []
        self.files = []
        self.dirs = []

    def tempfile(self):
        temporary_file = tempfile.NamedTemporaryFile("w+b", delete=False)
        self.files.append(temporary_file)
        self.paths.append(temporary_file.name)
        return temporary_file

    def tempdir(self):
        temporary_directory = tempfile.mkdtemp()
        self.dirs.append(temporary_directory)
        return temporary_directory

    def close(self):
        for fobj in self.files:
            fobj.close()
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)
        for dir_ in self.dirs:
            shutil.rmtree(dir_)


@contextlib.contextmanager
def _tempfile_manager():
    manager = TempfileManager()
    try:
        yield manager
    finally:
        manager.close()


@resource
def tempfile_resource(_init_context):
    with _tempfile_manager() as manager:
        yield manager
