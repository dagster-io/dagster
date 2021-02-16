import io
import random
from collections import defaultdict
from contextlib import contextmanager
from unittest import mock

from dagster_azure.blob import FakeBlobServiceClient

from .resources import ADLS2Resource
from .utils import ResourceNotFoundError


class FakeADLS2Resource(ADLS2Resource):
    """Stateful mock of an ADLS2Resource for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(
        self, account_name, credential="fake-creds"
    ):  # pylint: disable=unused-argument,super-init-not-called
        self._adls2_client = FakeADLS2ServiceClient(account_name)
        self._blob_client = FakeBlobServiceClient(account_name)


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
        self._file_system = defaultdict(FakeADLS2FileClient)
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
        return self._file_system[file_path]

    def create_file(self, file):
        return self._file_system[file]

    def delete_file(self, file):
        for k in list(self._file_system.keys()):
            if k.startswith(file):
                del self._file_system[k]


class FakeADLS2FileClient:
    """Stateful mock of an ADLS2 file client for testing."""

    def __init__(self):
        self.contents = None
        self.lease = None

    def get_file_properties(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        return {"lease": self.lease}

    def upload_data(self, contents, overwrite=False, lease=None):
        if self.lease is not None:
            if lease != self.lease:
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

    @contextmanager
    def acquire_lease(self, lease_duration=-1):  # pylint: disable=unused-argument
        if self.lease is None:
            self.lease = random.randint(0, 2 ** 9)
            try:
                yield self.lease
            finally:
                self.lease = None
        else:
            raise Exception("Lease already held")

    def download_file(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        return FakeADLS2FileDownloader(contents=self.contents)


class FakeADLS2FileDownloader:
    """Mock of an ADLS2 file downloader for testing."""

    def __init__(self, contents):
        self.contents = contents

    def readall(self):
        return self.contents

    def readinto(self, fileobj):
        fileobj.write(self.contents)
