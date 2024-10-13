import random
import string
import sys
import time

import pytest
from dagster._core.execution.compute_logs import should_disable_io_stream_redirect
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._time import get_current_datetime


class TestComputeLogManager:
    """You can extend this class to easily run these set of tests on any compute log manager. When
    extending, you simply need to override the `compute_log_manager` fixture and return your
    implementation of `ComputeLogManager`.

    For example:

    ```
    class TestMyComputeLogManagerImplementation(TestComputeLogManager):
        __test__ = True

        @pytest.fixture(scope='function', name='compute_log_manager')
        def compute_log_manager(self):
            return MyComputeLogManagerImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="compute_log_manager")
    def compute_log_manager(self):
        yield

    @pytest.fixture(name="write_manager")
    def write_manager(self):
        yield

    @pytest.fixture(name="read_manager")
    def read_manager(self):
        yield

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_capture(self, compute_log_manager):
        now = get_current_datetime()
        log_key = ["arbitrary", "log", "key", now.strftime("%Y_%m_%d__%H_%M_%S")]

        with compute_log_manager.capture_logs(log_key) as context:
            print("HELLO WORLD")  # noqa: T201
            print("HELLO ERROR", file=sys.stderr)  # noqa: T201
            assert not compute_log_manager.is_capture_complete(log_key)
            assert context.log_key == log_key

        assert compute_log_manager.is_capture_complete(log_key)

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"HELLO WORLD\n"
        assert log_data.stderr == b"HELLO ERROR\n"
        assert log_data.cursor

        log_metadata = compute_log_manager.get_log_metadata(log_key)
        assert log_metadata.stdout_location
        assert log_metadata.stderr_location
        assert log_metadata.stdout_download_url
        assert log_metadata.stderr_download_url

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_long_key(self, compute_log_manager):
        log_key = ["".join(random.choice(string.ascii_lowercase) for x in range(300))]

        with compute_log_manager.capture_logs(log_key) as context:
            print("HELLO WORLD")  # noqa: T201
            print("HELLO ERROR", file=sys.stderr)  # noqa: T201
            assert not compute_log_manager.is_capture_complete(log_key)
            assert context.log_key == log_key

        assert compute_log_manager.is_capture_complete(log_key)

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"HELLO WORLD\n"
        assert log_data.stderr == b"HELLO ERROR\n"
        assert log_data.cursor

        log_metadata = compute_log_manager.get_log_metadata(log_key)
        assert log_metadata.stdout_location
        assert log_metadata.stderr_location
        assert log_metadata.stdout_download_url
        assert log_metadata.stderr_download_url

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_streaming(self, write_manager, read_manager):
        from dagster._core.storage.cloud_storage_compute_log_manager import (
            CloudStorageComputeLogManager,
        )

        if (
            not isinstance(write_manager, CloudStorageComputeLogManager)
            or not isinstance(read_manager, CloudStorageComputeLogManager)
            or not write_manager.upload_interval
        ):
            pytest.skip("does not support streaming")

        now = get_current_datetime()
        log_key = ["streaming", "log", "key", now.strftime("%Y_%m_%d__%H_%M_%S")]
        with write_manager.capture_logs(log_key):
            print("hello stdout")  # noqa: T201
            print("hello stderr", file=sys.stderr)  # noqa: T201

            # read before the write manager has a chance to upload partial results
            log_data = read_manager.get_log_data(log_key)
            assert not log_data.stdout
            assert not log_data.stderr

            # wait past the upload interval and then read again
            time.sleep(write_manager.upload_interval + 1)
            log_data = read_manager.get_log_data(log_key)
            # print('WTF', log_data.stdout)
            assert log_data.stdout == b"hello stdout\n"
            assert log_data.stderr == b"hello stderr\n"

            # check the cloud storage directly that only partial keys have been uploaded
            assert not read_manager.cloud_storage_has_logs(log_key, ComputeIOType.STDOUT)
            assert not read_manager.cloud_storage_has_logs(log_key, ComputeIOType.STDOUT)
            assert read_manager.cloud_storage_has_logs(log_key, ComputeIOType.STDERR, partial=True)
            assert read_manager.cloud_storage_has_logs(log_key, ComputeIOType.STDERR, partial=True)

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_complete_checks(self, write_manager, read_manager):
        from dagster._core.storage.cloud_storage_compute_log_manager import (
            CloudStorageComputeLogManager,
        )

        if not isinstance(write_manager, CloudStorageComputeLogManager) or not isinstance(
            read_manager, CloudStorageComputeLogManager
        ):
            pytest.skip("unnecessary check since write/read manager should have the same behavior")

        now = get_current_datetime()
        log_key = ["complete", "test", "log", "key", now.strftime("%Y_%m_%d__%H_%M_%S")]
        with write_manager.capture_logs(log_key):
            print("hello stdout")  # noqa: T201
            print("hello stderr", file=sys.stderr)  # noqa: T201
            assert not write_manager.is_capture_complete(log_key)
            assert not read_manager.is_capture_complete(log_key)

        assert write_manager.is_capture_complete(log_key)
        assert read_manager.is_capture_complete(log_key)

    def test_log_stream(self, compute_log_manager):
        log_key = ["some", "log", "key"]
        with compute_log_manager.open_log_stream(log_key, ComputeIOType.STDOUT) as write_stream:
            write_stream.write("hello hello")
        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"hello hello"

    def test_delete_logs(self, compute_log_manager):
        log_key = ["some", "log", "key"]
        other_log_key = ["other", "log", "key"]
        with compute_log_manager.open_log_stream(log_key, ComputeIOType.STDOUT) as write_stream:
            write_stream.write("hello hello")
        with compute_log_manager.open_log_stream(
            other_log_key, ComputeIOType.STDOUT
        ) as write_stream:
            write_stream.write("hello hello")

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"hello hello"
        other_log_data = compute_log_manager.get_log_data(other_log_key)
        assert other_log_data.stdout == b"hello hello"

        compute_log_manager.delete_logs(log_key=log_key)

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout is None
        other_log_data = compute_log_manager.get_log_data(other_log_key)
        assert other_log_data.stdout == b"hello hello"

    def test_delete_log_prefix(self, compute_log_manager):
        log_key = ["some", "log", "key"]
        other_log_key = ["some", "log", "other_key"]
        with compute_log_manager.open_log_stream(log_key, ComputeIOType.STDOUT) as write_stream:
            write_stream.write("hello hello")
        with compute_log_manager.open_log_stream(
            other_log_key, ComputeIOType.STDOUT
        ) as write_stream:
            write_stream.write("hello hello")

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"hello hello"
        other_log_data = compute_log_manager.get_log_data(other_log_key)
        assert other_log_data.stdout == b"hello hello"

        compute_log_manager.delete_logs(prefix=["some", "log"])

        log_data = compute_log_manager.get_log_data(log_key)
        assert log_data.stdout is None
        other_log_data = compute_log_manager.get_log_data(other_log_key)
        assert other_log_data.stdout is None
