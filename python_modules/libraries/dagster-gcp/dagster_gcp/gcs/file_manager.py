import io
import uuid
from contextlib import contextmanager
from typing import Optional

import dagster._check as check
from dagster._core.storage.file_manager import (
    FileHandle,
    FileManager,
    TempfileManager,
    check_file_like_obj,
)
from google.cloud import storage


class GCSFileHandle(FileHandle):
    """A reference to a file on GCS."""

    def __init__(self, gcs_bucket: str, gcs_key: str):
        self._gcs_bucket = check.str_param(gcs_bucket, "gcs_bucket")
        self._gcs_key = check.str_param(gcs_key, "gcs_key")

    @property
    def gcs_bucket(self) -> str:
        """str: The name of the GCS bucket."""
        return self._gcs_bucket

    @property
    def gcs_key(self) -> str:
        """str: The GCS key."""
        return self._gcs_key

    @property
    def path_desc(self) -> str:
        """str: The file's GCS URL."""
        return self.gcs_path

    @property
    def gcs_path(self) -> str:
        """str: The file's GCS URL."""
        return f"gs://{self.gcs_bucket}/{self.gcs_key}"


class GCSFileManager(FileManager):
    def __init__(self, client, gcs_bucket, gcs_base_key):
        self._client = check.inst_param(client, "client", storage.client.Client)
        self._gcs_bucket = check.str_param(gcs_bucket, "gcs_bucket")
        self._gcs_base_key = check.str_param(gcs_base_key, "gcs_base_key")
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
            bucket_obj = self._client.bucket(file_handle.gcs_bucket)
            bucket_obj.blob(file_handle.gcs_key).download_to_file(temp_file_obj)
            temp_file_obj.flush()
            self._local_handle_cache[file_handle.gcs_path] = temp_name

        return file_handle

    @contextmanager
    def read(self, file_handle, mode="rb"):  # pyright: ignore[reportIncompatibleMethodOverride]
        check.inst_param(file_handle, "file_handle", GCSFileHandle)
        check.str_param(mode, "mode")
        check.param_invariant(mode in {"r", "rb"}, "mode")

        self._download_if_not_cached(file_handle)

        encoding = None if mode == "rb" else "utf-8"
        with open(self._get_local_path(file_handle), mode, encoding=encoding) as file_obj:
            yield file_obj

    def _file_handle_cached(self, file_handle):
        return file_handle.gcs_path in self._local_handle_cache

    def _get_local_path(self, file_handle):
        return self._local_handle_cache[file_handle.gcs_path]

    def read_data(self, file_handle):
        with self.read(file_handle, mode="rb") as file_obj:
            return file_obj.read()

    def write_data(self, data, ext=None, key: Optional[str] = None):
        key = check.opt_str_param(key, "key", default=str(uuid.uuid4()))
        check.inst_param(data, "data", bytes)
        return self.write(io.BytesIO(data), mode="wb", key=key, ext=ext)

    def write(self, file_obj, mode="wb", ext=None, key: Optional[str] = None):
        key = check.opt_str_param(key, "key", default=str(uuid.uuid4()))
        check_file_like_obj(file_obj)
        gcs_key = self.get_full_key(key + (("." + ext) if ext is not None else ""))
        bucket_obj = self._client.bucket(self._gcs_bucket)
        bucket_obj.blob(gcs_key).upload_from_file(file_obj)
        return GCSFileHandle(self._gcs_bucket, gcs_key)

    def get_full_key(self, file_key):
        return f"{self._gcs_base_key}/{file_key}"

    def delete_local_temp(self):
        self._temp_file_manager.close()
