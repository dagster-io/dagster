import random
import string
import sys

import pytest

from dagster._core.execution.compute_logs import should_disable_io_stream_redirect


class TestCapturedLogManager:
    """
    You can extend this class to easily run these set of tests on any compute log manager. When
    extending, you simply need to override the `compute_log_manager` fixture and return your
    implementation of `CapturedLogManager`.

    For example:

    ```
    class TestMyComputeLogManagerImplementation(TestCapturedLogManager):
        __test__ = True

        @pytest.fixture(scope='function', name='captured_log_manager')
        def captured_log_manager(self):  # pylint: disable=arguments-differ
            return MyCapturedLogManagerImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="captured_log_manager")
    def captured_log_manager(self):
        yield

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_capture(self, captured_log_manager):
        log_key = ["foo"]

        with captured_log_manager.capture_logs(log_key):
            print("HELLO WORLD")  # pylint: disable=print-call
            print("HELLO ERROR", file=sys.stderr)  # pylint: disable=print-call
            assert not captured_log_manager.is_capture_complete(log_key)

        assert captured_log_manager.is_capture_complete(log_key)

        log_data = captured_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"HELLO WORLD\n"
        assert log_data.stderr == b"HELLO ERROR\n"
        assert log_data.cursor

        log_metadata = captured_log_manager.get_contextual_log_metadata(log_key)
        assert log_metadata.stdout_location
        assert log_metadata.stderr_location
        assert log_metadata.stdout_download_url
        assert log_metadata.stderr_download_url

    @pytest.mark.skipif(
        should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
    )
    def test_long_key(self, captured_log_manager):
        log_key = ["".join(random.choice(string.ascii_lowercase) for x in range(300))]

        with captured_log_manager.capture_logs(log_key):
            print("HELLO WORLD")  # pylint: disable=print-call
            print("HELLO ERROR", file=sys.stderr)  # pylint: disable=print-call
            assert not captured_log_manager.is_capture_complete(log_key)

        assert captured_log_manager.is_capture_complete(log_key)

        log_data = captured_log_manager.get_log_data(log_key)
        assert log_data.stdout == b"HELLO WORLD\n"
        assert log_data.stderr == b"HELLO ERROR\n"
        assert log_data.cursor

        log_metadata = captured_log_manager.get_contextual_log_metadata(log_key)
        assert log_metadata.stdout_location
        assert log_metadata.stderr_location
        assert log_metadata.stdout_download_url
        assert log_metadata.stderr_download_url
