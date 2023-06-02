import io
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import BinaryIO, ContextManager, Iterator, Optional, TextIO, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._config import Field, StringSource
from dagster._core.definitions.resource_definition import dagster_maintained_resource, resource
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.instance import DagsterInstance
from dagster._utils import mkdir_p

from .temp_file_manager import TempfileManager

IOStream: TypeAlias = Union[TextIO, BinaryIO]


class FileHandle(ABC):
    """A reference to a file as manipulated by a FileManager.

    Subclasses may handle files that are resident on the local file system, in an object store, or
    in any arbitrary place where a file can be stored.

    This exists to handle the very common case where you wish to write a computation that reads,
    transforms, and writes files, but where you also want the same code to work in local development
    as well as on a cluster where the files will be stored in a globally available object store
    such as S3.
    """

    @public
    @property
    @abstractmethod
    def path_desc(self) -> str:
        """A representation of the file path for display purposes only."""
        raise NotImplementedError()


class LocalFileHandle(FileHandle):
    """A reference to a file on a local filesystem."""

    def __init__(self, path: str):
        self._path = check.str_param(path, "path")

    @public
    @property
    def path(self) -> str:
        """The file's path."""
        return self._path

    @public
    @property
    def path_desc(self) -> str:
        """A representation of the file path for display purposes only."""
        return self._path


class FileManager(ABC):
    """Base class for all file managers in dagster.

    The file manager is an interface that can be implemented by resources to provide abstract
    access to a file system such as local disk, S3, or other cloud storage.

    For examples of usage, see the documentation of the concrete file manager implementations.
    """

    @public
    @abstractmethod
    def copy_handle_to_local_temp(self, file_handle: FileHandle) -> str:
        """Copy a file represented by a file handle to a temp file.

        In an implementation built around an object store such as S3, this method would be expected
        to download the file from S3 to local filesystem in a location assigned by the standard
        library's :py:mod:`python:tempfile` module.

        Temp files returned by this method are *not* guaranteed to be reusable across solid
        boundaries. For files that must be available across solid boundaries, use the
        :py:meth:`~dagster._core.storage.file_manager.FileManager.read`,
        :py:meth:`~dagster._core.storage.file_manager.FileManager.read_data`,
        :py:meth:`~dagster._core.storage.file_manager.FileManager.write`, and
        :py:meth:`~dagster._core.storage.file_manager.FileManager.write_data` methods.

        Args:
            file_handle (FileHandle): The handle to the file to make available as a local temp file.

        Returns:
            str: Path to the local temp file.
        """
        raise NotImplementedError()

    @public
    @abstractmethod
    def delete_local_temp(self) -> None:
        """Delete all local temporary files created by previous calls to
        :py:meth:`~dagster._core.storage.file_manager.FileManager.copy_handle_to_local_temp`.

        Should typically only be called by framework implementors.
        """
        raise NotImplementedError()

    @public
    @abstractmethod
    def read(self, file_handle: FileHandle, mode: str = "rb") -> ContextManager[IOStream]:
        """Return a file-like stream for the file handle.

        This may incur an expensive network call for file managers backed by object stores
        such as S3.

        Args:
            file_handle (FileHandle): The file handle to make available as a stream.
            mode (str): The mode in which to open the file. Default: ``"rb"``.

        Returns:
            Union[TextIO, BinaryIO]: A file-like stream.
        """
        raise NotImplementedError()

    @public
    @abstractmethod
    def read_data(self, file_handle: FileHandle) -> bytes:
        """Return the bytes for a given file handle. This may incur an expensive network
        call for file managers backed by object stores such as s3.

        Args:
            file_handle (FileHandle): The file handle for which to return bytes.

        Returns:
            bytes: Bytes for a given file handle.
        """
        raise NotImplementedError()

    @public
    @abstractmethod
    def write(self, file_obj: IOStream, mode: str = "wb", ext: Optional[str] = None) -> FileHandle:
        """Write the bytes contained within the given file object into the file manager.

        Args:
            file_obj (Union[TextIO, StringIO]): A file-like object.
            mode (Optional[str]): The mode in which to write the file into the file manager.
                Default: ``"wb"``.
            ext (Optional[str]): For file managers that support file extensions, the extension with
                which to write the file. Default: ``None``.

        Returns:
            FileHandle: A handle to the newly created file.
        """
        raise NotImplementedError()

    @public
    @abstractmethod
    def write_data(self, data: bytes, ext: Optional[str] = None) -> FileHandle:
        """Write raw bytes into the file manager.

        Args:
            data (bytes): The bytes to write into the file manager.
            ext (Optional[str]): For file managers that support file extensions, the extension with
                which to write the file. Default: ``None``.

        Returns:
            FileHandle: A handle to the newly created file.
        """
        raise NotImplementedError()


@dagster_maintained_resource
@resource(config_schema={"base_dir": Field(StringSource, is_required=False)})
def local_file_manager(init_context: InitResourceContext) -> "LocalFileManager":
    """FileManager that provides abstract access to a local filesystem.

    By default, files will be stored in `<local_artifact_storage>/storage/file_manager` where
    `<local_artifact_storage>` can be configured the ``dagster.yaml`` file in ``$DAGSTER_HOME``.

    Implements the :py:class:`~dagster._core.storage.file_manager.FileManager` API.

    Examples:
        .. code-block:: python

            import tempfile

            from dagster import job, local_file_manager, op


            @op(required_resource_keys={"file_manager"})
            def write_files(context):
                fh_1 = context.resources.file_manager.write_data(b"foo")

                with tempfile.NamedTemporaryFile("w+") as fd:
                    fd.write("bar")
                    fd.seek(0)
                    fh_2 = context.resources.file_manager.write(fd, mode="w", ext=".txt")

                return (fh_1, fh_2)


            @op(required_resource_keys={"file_manager"})
            def read_files(context, file_handles):
                fh_1, fh_2 = file_handles
                assert context.resources.file_manager.read_data(fh_2) == b"bar"
                fd = context.resources.file_manager.read(fh_2, mode="r")
                assert fd.read() == "foo"
                fd.close()


            @job(resource_defs={"file_manager": local_file_manager})
            def files_pipeline():
                read_files(write_files())

        Or to specify the file directory:

        .. code-block:: python

            @job(
                resource_defs={
                    "file_manager": local_file_manager.configured({"base_dir": "/my/base/dir"})
                }
            )
            def files_pipeline():
                read_files(write_files())
    """
    return LocalFileManager(
        base_dir=init_context.resource_config.get(
            "base_dir", os.path.join(init_context.instance.storage_directory(), "file_manager")  # type: ignore  # (possible none)
        )
    )


def check_file_like_obj(obj: object) -> None:
    check.invariant(obj and hasattr(obj, "read") and hasattr(obj, "write"))


class LocalFileManager(FileManager):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._base_dir_ensured = False
        self._temp_file_manager = TempfileManager()

    @staticmethod
    def for_instance(instance: DagsterInstance, run_id: str) -> "LocalFileManager":
        check.inst_param(instance, "instance", DagsterInstance)
        return LocalFileManager(instance.file_manager_directory(run_id))

    def ensure_base_dir_exists(self) -> None:
        if self._base_dir_ensured:
            return

        mkdir_p(self.base_dir)

        self._base_dir_ensured = True

    def copy_handle_to_local_temp(self, file_handle: FileHandle) -> str:
        check.inst_param(file_handle, "file_handle", FileHandle)
        with self.read(file_handle, "rb") as handle_obj:  # type: ignore  # (??)
            temp_file_obj = self._temp_file_manager.tempfile()
            temp_file_obj.write(handle_obj.read())
            temp_name = temp_file_obj.name
            temp_file_obj.close()
            return temp_name

    @contextmanager
    def read(self, file_handle: LocalFileHandle, mode: str = "rb") -> Iterator[IOStream]:
        check.inst_param(file_handle, "file_handle", LocalFileHandle)
        check.str_param(mode, "mode")
        check.param_invariant(mode in {"r", "rb"}, "mode")

        encoding = None if mode == "rb" else "utf8"
        with open(file_handle.path, mode, encoding=encoding) as file_obj:
            yield file_obj  # type: ignore  # (??)

    def read_data(self, file_handle: LocalFileHandle) -> bytes:
        with self.read(file_handle, mode="rb") as file_obj:
            return file_obj.read()  # type: ignore  # (??)

    def write_data(self, data: bytes, ext: Optional[str] = None):
        check.inst_param(data, "data", bytes)
        return self.write(io.BytesIO(data), mode="wb", ext=ext)

    def write(
        self, file_obj: IOStream, mode: str = "wb", ext: Optional[str] = None
    ) -> LocalFileHandle:
        check_file_like_obj(file_obj)
        check.opt_str_param(ext, "ext")

        self.ensure_base_dir_exists()

        dest_file_path = os.path.join(
            self.base_dir, str(uuid.uuid4()) + (("." + ext) if ext is not None else "")
        )

        encoding = None if "b" in mode else "utf8"
        with open(dest_file_path, mode, encoding=encoding) as dest_file_obj:
            shutil.copyfileobj(file_obj, dest_file_obj)  # type: ignore  # (??)
            return LocalFileHandle(dest_file_path)

    def delete_local_temp(self) -> None:
        self._temp_file_manager.close()
