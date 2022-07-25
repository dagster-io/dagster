import io
import uuid
from contextlib import contextmanager

import dagster._check as check
from dagster._core.storage.file_manager import (
    FileHandle,
    FileManager,
    TempfileManager,
    check_file_like_obj,
)


class S3FileHandle(FileHandle):
    """A reference to a file on S3."""

    def __init__(self, s3_bucket: str, s3_key: str):
        self._s3_bucket = check.str_param(s3_bucket, "s3_bucket")
        self._s3_key = check.str_param(s3_key, "s3_key")

    @property
    def s3_bucket(self) -> str:
        """str: The name of the S3 bucket."""
        return self._s3_bucket

    @property
    def s3_key(self) -> str:
        """str: The S3 key."""
        return self._s3_key

    @property
    def path_desc(self) -> str:
        """str: The file's S3 URL."""
        return self.s3_path

    @property
    def s3_path(self) -> str:
        """str: The file's S3 URL."""
        return "s3://{bucket}/{key}".format(bucket=self.s3_bucket, key=self.s3_key)


class S3FileManager(FileManager):
    def __init__(self, s3_session, s3_bucket, s3_base_key):
        self._s3_session = s3_session
        self._s3_bucket = check.str_param(s3_bucket, "s3_bucket")
        self._s3_base_key = check.str_param(s3_base_key, "s3_base_key")
        self._local_handle_cache = {}
        self._temp_file_manager = TempfileManager()

    def copy_handle_to_local_temp(self, file_handle):
        self._download_if_not_cached(file_handle)
        return self._get_local_path(file_handle)

    def _download_if_not_cached(self, file_handle):
        if not self._file_handle_cached(file_handle):
            # instigate download
            temp_file_obj = self._temp_file_manager.tempfile()
            temp_name = temp_file_obj.name
            self._s3_session.download_file(
                Bucket=file_handle.s3_bucket, Key=file_handle.s3_key, Filename=temp_name
            )
            self._local_handle_cache[file_handle.s3_path] = temp_name

        return file_handle

    @contextmanager
    def read(self, file_handle, mode="rb"):
        check.inst_param(file_handle, "file_handle", S3FileHandle)
        check.str_param(mode, "mode")
        check.param_invariant(mode in {"r", "rb"}, "mode")

        self._download_if_not_cached(file_handle)

        encoding = None if mode == "rb" else "utf-8"
        with open(self._get_local_path(file_handle), mode, encoding=encoding) as file_obj:
            yield file_obj

    def _file_handle_cached(self, file_handle):
        return file_handle.s3_path in self._local_handle_cache

    def _get_local_path(self, file_handle):
        return self._local_handle_cache[file_handle.s3_path]

    def read_data(self, file_handle):
        with self.read(file_handle, mode="rb") as file_obj:
            return file_obj.read()

    def write_data(self, data, ext=None):
        check.inst_param(data, "data", bytes)
        return self.write(io.BytesIO(data), mode="wb", ext=ext)

    def write(self, file_obj, mode="wb", ext=None):
        check_file_like_obj(file_obj)
        s3_key = self.get_full_key(str(uuid.uuid4()) + (("." + ext) if ext is not None else ""))
        self._s3_session.put_object(Body=file_obj, Bucket=self._s3_bucket, Key=s3_key)
        return S3FileHandle(self._s3_bucket, s3_key)

    def get_full_key(self, file_key):
        return "{base_key}/{file_key}".format(base_key=self._s3_base_key, file_key=file_key)

    def delete_local_temp(self):
        self._temp_file_manager.close()
