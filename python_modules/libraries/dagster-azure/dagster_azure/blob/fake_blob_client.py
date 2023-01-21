import io
import random
from contextlib import contextmanager
from dataclasses import dataclass
from unittest import mock

from .utils import ResourceNotFoundError


class FakeBlobServiceClient:
    """Stateful mock of an Blob service client for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(self, account_name, credential="fake-creds"):
        self._account_name = account_name
        self._credential = mock.MagicMock()
        self._credential.account_key = credential
        self._containers = {}

    @property
    def account_name(self):
        return self._account_name

    @property
    def credential(self):
        return self._credential

    @property
    def containers(self):
        return self._containers

    def get_container_client(self, container):
        return self._containers.setdefault(
            container, FakeBlobContainerClient(self.account_name, container)
        )

    def get_blob_client(self, container, blob):
        return self.get_container_client(container).get_blob_client(blob)


@dataclass
class FakeBlob:
    name: str
    url: str


class FakeBlobContainerClient:
    """Stateful mock of an Blob container client for testing."""

    def __init__(self, account_name, container_name):
        self._container = {}
        self._account_name = account_name
        self._container_name = container_name

    @property
    def account_name(self):
        return self._account_name

    @property
    def container_name(self):
        return self._container_name

    def keys(self):
        return self._container.keys()

    def get_container_properties(self):
        return {"account_name": self.account_name, "container_name": self.container_name}

    def has_blob(self, blob_key):
        return bool(self._container.get(blob_key))

    def get_blob_client(self, blob_key):
        if blob_key not in self._container:
            blob = self.create_blob(blob_key)
        else:
            blob = self._container[blob_key]
        return blob

    def create_blob(self, blob_key):
        blob = FakeBlobClient()
        self._container[blob_key] = blob
        return blob

    def list_blobs(self, name_starts_with=None):
        for k, v in self._container.items():
            if name_starts_with is None or k.startswith(name_starts_with):
                yield FakeBlob(name=k, url=v.contents)

    def delete_blob(self, prefix):
        # Use list to avoid mutating dict as we iterate
        for k in list(self._container.keys()):
            if k.startswith(prefix):
                del self._container[k]

    def delete_blobs(self, *keys):
        for key in keys:
            if key in self._container:
                del self._container[key]


class FakeBlobClient:
    """Stateful mock of an Blob blob client for testing."""

    def __init__(self):
        self.contents = None
        self.lease = None

    def start_copy_from_url(self, url):
        self.contents = url

    def get_blob_properties(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        return {"lease": self.lease}

    def upload_blob(self, contents, overwrite=False, lease=None):
        if self.lease is not None:
            if lease != self.lease:
                raise Exception("Invalid lease!")
        if self.contents is None or overwrite is True:
            if isinstance(contents, str):
                self.contents = contents.encode("utf8")
            elif isinstance(contents, io.TextIOBase):
                self.contents = contents.read().encode("utf8")
            elif isinstance(contents, io.IOBase):
                self.contents = contents.read()
            elif isinstance(contents, bytes):
                self.contents = contents
            # Python 2 compatibility - no base class for `file` type
            elif hasattr(contents, "read"):
                self.contents = contents.read()
            else:
                self.contents = contents

    @property
    def url(self):
        return ":memory:"

    @contextmanager
    def acquire_lease(self, lease_duration=-1):  # pylint: disable=unused-argument
        if self.lease is None:
            self.lease = random.randint(0, 2**9)
            try:
                yield self.lease
            finally:
                self.lease = None
        else:
            raise Exception("Lease already held")

    def download_blob(self):
        if self.contents is None:
            raise ResourceNotFoundError("File does not exist!")
        return FakeBlobDownloader(contents=self.contents)


class FakeBlobDownloader:
    """Mock of a Blob file downloader for testing."""

    def __init__(self, contents):
        self.contents = contents

    def readall(self):
        return self.contents

    def readinto(self, fileobj):
        fileobj.write(self.contents)
