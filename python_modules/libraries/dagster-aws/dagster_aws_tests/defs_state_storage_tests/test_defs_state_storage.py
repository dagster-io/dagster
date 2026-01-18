import fsspec
import pytest
import s3fs
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.defs_state.blob_storage_state_storage import UPathDefsStateStorage
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster_shared import check
from moto.moto_server.threaded_moto_server import ThreadedMotoServer

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.defs_state_storage import TestDefsStateStorage

_MOCK_STORAGE_OPTIONS = {
    "anon": False,
    "key": "fake",
    "secret": "fake",
    "client_kwargs": {"endpoint_url": "http://localhost:5001"},
}


@pytest.fixture(scope="class", autouse=True)
def moto_s3_autopatch():
    """Because s3fs doesn't play nicely with moto, we need some additional mocking to get it to work."""
    server = ThreadedMotoServer(port=5001)
    server.start()

    fsspec.register_implementation("s3", s3fs.S3FileSystem, clobber=True)

    yield

    server.stop()


class TestS3UPathDefsStateStorage(TestDefsStateStorage):
    """Tests the blob storage state storage implementation."""

    __test__ = True

    @pytest.fixture(name="storage", scope="function")
    def state_storage(self, mock_s3_bucket):
        with instance_for_test(
            overrides={
                "defs_state_storage": {
                    "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                    "class": "UPathDefsStateStorage",
                    "config": {
                        "base_path": f"s3://{mock_s3_bucket.name}/foo",
                        "storage_options": _MOCK_STORAGE_OPTIONS,
                    },
                }
            }
        ) as instance:
            state_storage = check.inst(instance.defs_state_storage, UPathDefsStateStorage)

            # Check that we have an S3 filesystem
            assert state_storage.base_path.fs.__class__.__name__ == "S3FileSystem"
            yield state_storage
