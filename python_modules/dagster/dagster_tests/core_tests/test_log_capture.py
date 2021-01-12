import sys

import pytest
from dagster.core.execution.compute_logs import (
    mirror_stream_to_file,
    should_disable_io_stream_redirect,
)
from dagster.utils.test import get_temp_file_name


@pytest.mark.skipif(
    should_disable_io_stream_redirect(), reason="compute logs disabled for win / py3.6+"
)
def test_capture():
    with get_temp_file_name() as capture_filepath:
        with mirror_stream_to_file(sys.stdout, capture_filepath):
            print("HELLO")

        with open(capture_filepath, "r") as capture_stream:
            assert "HELLO" in capture_stream.read()
