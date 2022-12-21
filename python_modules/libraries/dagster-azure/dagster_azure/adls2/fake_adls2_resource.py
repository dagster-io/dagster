import io
import random
from typing import Dict
from unittest import mock

from dagster import resource

from dagster_azure.blob import FakeBlobServiceClient

from .resources import ADLS2Resource
from .utils import ResourceNotFoundError


@resource({"account_name": str})
def fake_adls2_resource(context):
    return FakeADLS2Resource(account_name=context.resource_config["account_name"])


class FakeADLS2Resource(ADLS2Resource):
    """Stateful mock of an ADLS2Resource for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(
        self, account_name, credential="fake-creds"
    ):  # pylint: disable=unused-argument,super-init-not-called
        self._adls2_client = FakeADLS2ServiceClient(account_name)
        self._blob_client = FakeBlobServiceClient(account_name)
        self._lease_client_constructor = FakeLeaseClient


class FakeLeaseClient:
    def __init__(self, client):
        self.client = client
        self.id = None

        # client needs a ref to self to check if a given lease is valid
        self.client._lease = self

    def acquire(self, lease_duration=-1):  # pylint: disable=unused-argument
        if self.id is None:
            self.id = random.randint(0, 2**9)
        else:
            raise Exception("Lease already held")

    def release(self):
        self.id = None

    def is_valid(self, lease):
        if self.id is None:
            # no lease is held so any operation is valid
            return True
        return lease == self.id


class FakeADLS2ServiceClient:
    """Stateful mock of an ADLS2 service client for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(self, account_name, credential="fake-creds"):
        self._account_name = account_name
        self._credential = mock.MagicMock()
        self._credential.account_key = credential
        self._file_systems = {}

    @property
    def account_name(self):
        return self._account_name

    @property
    def credential(self):
        return self._credential

    @property
    def file_systems(self):
        return self._file_systems

    def get_file_system_client(self, file_system):
        return self._file_systems.setdefault(
            file_system, FakeADLS2FilesystemClient(self.account_name, file_system)
        )

    def get_file_client(self, file_system, file_path):
        return self.get_file_system_client(file_system).get_file_client(file_path)


class FakeADLS2FilesystemClient:
    """Stateful mock of an ADLS2 filesystem client for testing."""

    def __init__(self, account_name, file_system_name):
        self._file_system: Dict[str, FakeADLS2FileClient] = {}
        self._account_name = account_name
        self._file_system_name = file_system_name

    @property
    def account_name(self):
        return self._account_name

    @property
    def file_system_name(self):
        return self._file_system_name

    def keys(self):
        return self._file_system.keys()

    def get_file_system_properties(self):
        return {"account_name": self.account_name, "file_system_name": self.file_system_name}

    def has_file(self, path):
        return bool(self._file_system.get(path))

    def get_file_client(self, file_path):
        # pass fileclient a ref to self and its name so the file can delete itself
        self._file_system.setdefault(file_path, FakeADLS2FileClient(self, file_path))
        return self._file_system[file_path]

    def create_file(self, file):
        # pass fileclient a ref to self and the file's name so the file can delete itself by
        # accessing the self._file_system dict
        self._file_system.setdefault(file, FakeADLS2FileClient(fs_client=self, name=file))
        return self._file_system[file]

    def delete_file(self, file):
        for k in list(self._file_system.keys()):
            if k.startswith(file):
                del self._file_system[k]


class FakeADLS2FileClient:
    """Stateful mock of an ADLS2 file client for testing."""

    def __init__(self, name, fs_client):
        self.name = name
        self.contents = None
        self._lease = None
        self.fs_client = fs_client

    @property
    def lease(self):
        return self._lease if self._lease is None else self._lease.id

    def get_file_properties(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        lease_id = None if self._lease is None else self._lease.id
        return {"lease": lease_id}

    def upload_data(self, contents, overwrite=False, lease=None):
        if self._lease is not None:
            if not self._lease.is_valid(lease):
                raise Exception("Invalid lease!")
        if self.contents is not None or overwrite is True:
            if isinstance(contents, str):
                self.contents = contents.encode("utf8")
            elif isinstance(contents, io.BytesIO):
                self.contents = contents.read()
            elif isinstance(contents, io.StringIO):
                self.contents = contents.read().encode("utf8")
            elif isinstance(contents, bytes):
                self.contents = contents
            else:
                self.contents = contents

    def download_file(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        return FakeADLS2FileDownloader(contents=self.contents)

    def delete_file(self, lease=None):
        if self._lease is not None:
            if not self._lease.is_valid(lease):
                raise Exception("Invalid lease!")
        self.fs_client.delete_file(self.name)


class FakeADLS2FileDownloader:
    """Mock of an ADLS2 file downloader for testing."""

    def __init__(self, contents):
        self.contents = contents

    def readall(self):
        return self.contents

    def readinto(self, fileobj):
        fileobj.write(self.contents)
