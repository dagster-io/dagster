import warnings

from dagster import resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource

from dagster_azure.fakes.fake_adls2_resource import (
    FakeADLS2FileClient as FakeADLS2FileClientBase,
    FakeADLS2FileDownloader as FakeADLS2FileDownloaderBase,
    FakeADLS2FilesystemClient as FakeADLS2FilesystemClientBase,
    FakeADLS2Resource as FakeADLS2ResourceBase,
    FakeADLS2ServiceClient as FakeADLS2ServiceClientBase,
    FakeLeaseClient as FakeLeaseClientBase,
)


@dagster_maintained_resource
@resource({"account_name": str})
def fake_adls2_resource(context):
    return FakeADLS2Resource(account_name=context.resource_config["account_name"])


DEPRECATION_WARNING = "Fake class imports from dagster_azure.adls2 are deprecated and will be removed in a next minor release (1.10.0). Please use dagster_azure.fakes path instead"


class FakeADLS2Resource(FakeADLS2ResourceBase):
    """Stateful mock of an ADLS2Resource for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(self, **kwargs):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(**kwargs)


class FakeLeaseClient(FakeLeaseClientBase):
    def __init__(self, client):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(client)


class FakeADLS2ServiceClient(FakeADLS2ServiceClientBase):
    """Stateful mock of an ADLS2 service client for testing.

    Wraps a ``mock.MagicMock``. Containers are implemented using an in-memory dict.
    """

    def __init__(self, account_name, credential="fake-creds"):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(account_name, credential)


class FakeADLS2FilesystemClient(FakeADLS2FilesystemClientBase):
    """Stateful mock of an ADLS2 filesystem client for testing."""

    def __init__(self, account_name, file_system_name):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(account_name, file_system_name)


class FakeADLS2FileClient(FakeADLS2FileClientBase):
    """Stateful mock of an ADLS2 file client for testing."""

    def __init__(self, name, fs_client):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(name, fs_client)


class FakeADLS2FileDownloader(FakeADLS2FileDownloaderBase):
    """Mock of an ADLS2 file downloader for testing."""

    def __init__(self, contents):
        warnings.warn(DEPRECATION_WARNING, DeprecationWarning, stacklevel=2)
        super().__init__(contents)
