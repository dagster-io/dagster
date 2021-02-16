import io
import random
from collections import defaultdict
from contextlib import contextmanager
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


class FakeBlobContainerClient:
    """Stateful mock of an Blob container client for testing."""

    def __init__(self, account_name, container_name):
        self._container = defaultdict(FakeBlobClient)
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

    def has_blob(self, path):
        return bool(self._container.get(path))

    def get_blob_client(self, blob):
        return self._container[blob]

    def create_blob(self, blob):
        return self._container[blob]

    def list_blobs(self, name_starts_with=None):
        for k, v in self._container.items():
            if name_starts_with is None or k.startswith(name_starts_with):
                yield {
                    "name": k,
                    # This clearly isn't actually the URL but we need a way of copying contents
                    # across blobs and this allows us to do it
                    "url": v.contents,
                }

    def delete_blob(self, blob):
        # Use list to avoid mutating dict as we iterate
        for k in list(self._container.keys()):
            if k.startswith(blob):
                del self._container[k]


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
            self.lease = random.randint(0, 2 ** 9)
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
