import io
import uuid
from contextlib import contextmanager
from typing import Any, Optional

import dagster._check as check
from dagster._core.storage.file_manager import (
    FileHandle,
    FileManager,
    TempfileManager,
    check_file_like_obj,
)

from dagster_azure.adls2.utils import DataLakeServiceClient


class ADLS2FileHandle(FileHandle):
    """A reference to a file on ADLS2."""

    def __init__(self, account: str, file_system: str, key: str):
        self._account = check.str_param(account, "account")
        self._file_system = check.str_param(file_system, "file_system")
        self._key = check.str_param(key, "key")

    @property
    def account(self) -> str:
        """str: The name of the ADLS2 account."""
        return self._account

    @property
    def file_system(self) -> str:
        """str: The name of the ADLS2 file system."""
        return self._file_system

    @property
    def key(self) -> str:
        """str: The ADLS2 key."""
        return self._key

    @property
    def path_desc(self) -> str:
        """str: The file's ADLS2 URL."""
        return self.adls2_path

    @property
    def adls2_path(self) -> str:
        """str: The file's ADLS2 URL."""
        return f"adfss://{self.file_system}@{self.account}.dfs.core.windows.net/{self.key}"


class ADLS2FileManager(FileManager):
    def __init__(self, adls2_client: DataLakeServiceClient, file_system: str, prefix: str):
        self._client = adls2_client
        self._file_system = check.str_param(file_system, "file_system")
        self._prefix = check.str_param(prefix, "prefix")
        self._local_handle_cache: dict[str, str] = {}
        self._temp_file_manager = TempfileManager()

    def copy_handle_to_local_temp(self, file_handle: ADLS2FileHandle):
        self._download_if_not_cached(file_handle)
        return self._get_local_path(file_handle)

    def _download_if_not_cached(self, file_handle: ADLS2FileHandle):
        if not self._file_handle_cached(file_handle):
            # instigate download
            temp_file_obj = self._temp_file_manager.tempfile()
            temp_name = temp_file_obj.name
            file = self._client.get_file_client(
                file_system=file_handle.file_system,
                file_path=file_handle.key,
            )
            download = file.download_file()
            with open(temp_name, "wb") as file_obj:
                download.readinto(file_obj)
            self._local_handle_cache[file_handle.adls2_path] = temp_name

        return file_handle

    @contextmanager
    def read(self, file_handle: ADLS2FileHandle, mode: str = "rb"):
        check.inst_param(file_handle, "file_handle", ADLS2FileHandle)
        check.str_param(mode, "mode")
        check.param_invariant(mode in {"r", "rb"}, "mode")

        self._download_if_not_cached(file_handle)

        encoding = None if "b" in mode else "utf-8"
        with open(self._get_local_path(file_handle), mode, encoding=encoding) as file_obj:
            yield file_obj

    def _file_handle_cached(self, file_handle: ADLS2FileHandle) -> bool:
        return file_handle.adls2_path in self._local_handle_cache

    def _get_local_path(self, file_handle: ADLS2FileHandle) -> str:
        return self._local_handle_cache[file_handle.adls2_path]

    def read_data(self, file_handle: ADLS2FileHandle) -> Any:
        with self.read(file_handle, mode="rb") as file_obj:
            return file_obj.read()

    def write_data(self, data: bytes, ext: Optional[str] = None) -> ADLS2FileHandle:
        check.inst_param(data, "data", bytes)
        return self.write(io.BytesIO(data), mode="wb", ext=ext)

    def write(
        self, file_obj: io.BytesIO, mode: str = "wb", ext: Optional[str] = None
    ) -> ADLS2FileHandle:
        check_file_like_obj(file_obj)
        adls2_key = self.get_full_key(str(uuid.uuid4()) + (("." + ext) if ext is not None else ""))
        adls2_file = self._client.get_file_client(
            file_system=self._file_system, file_path=adls2_key
        )
        adls2_file.upload_data(file_obj, overwrite=True)
        account_name = check.not_none(self._client.account_name, "Expected account name to be set")
        return ADLS2FileHandle(account_name, self._file_system, adls2_key)

    def get_full_key(self, file_key: str) -> str:
        return f"{self._prefix}/{file_key}"

    def delete_local_temp(self) -> None:
        self._temp_file_manager.close()
