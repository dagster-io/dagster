from collections.abc import Iterator

import pytest

from dagster_azure_tests.pipes_tests.mock_blob_storage import MockBlobServiceClient
from dagster_azure_tests.pipes_tests.utils import temp_script


@pytest.fixture
def storage_account_name():
    return "fakeazureblobstorageaccount"


@pytest.fixture
def container_name():
    return "fakecontainer"


@pytest.fixture
def external_script() -> Iterator[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os  # noqa
        import time
        import tempfile
        from dagster_pipes import (
            PipesAzureBlobStorageContextLoader,
            PipesAzureBlobStorageMessageWriter,
            open_dagster_pipes,
        )

        client = MockBlobServiceClient(
            temp_dir=tempfile.gettempdir(), storage_account="fakeazureblobstorageaccount"
        )

        context_loader = PipesAzureBlobStorageContextLoader(client=client)
        message_writer = PipesAzureBlobStorageMessageWriter(client=client, interval=0.001)

        with open_dagster_pipes(
            context_loader=context_loader, message_writer=message_writer
        ) as context:
            context.log.info("hello world")
            time.sleep(
                0.1
            )  # sleep to make sure that we encompass multiple intervals for blob storage io
            context.report_asset_materialization(
                metadata={"bar": {"raw_value": context.get_extra("bar"), "type": "md"}},
                data_version="alpha",
            )
            context.report_asset_check(
                "foo_check",
                passed=True,
                severity="WARN",
                metadata={
                    "meta_1": 1,
                    "meta_2": {"raw_value": "foo", "type": "text"},
                },
            )

    with temp_script(script_fn, MockBlobServiceClient) as script_path:
        yield script_path
