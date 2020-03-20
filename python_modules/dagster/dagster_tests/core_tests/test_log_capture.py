from __future__ import print_function

import time

from contextlib2 import ExitStack

from dagster.core.execution.compute_logs import mirror_stream_to_file
from dagster.utils.test import get_temp_file_name


def test_capture():
    stack = ExitStack()
    capture_filepath = stack.enter_context(get_temp_file_name())
    mirror_filepath = stack.enter_context(get_temp_file_name())
    capture_stream = stack.enter_context(open(capture_filepath, 'a+', buffering=1))
    stack.enter_context(mirror_stream_to_file(capture_stream, mirror_filepath))
    print('HELLO', file=capture_stream)
    time.sleep(1)
    with open(capture_filepath, 'r') as out_stream:
        assert 'HELLO' in out_stream.read()
    with open(mirror_filepath, 'r') as mirror_stream:
        assert 'HELLO' in mirror_stream.read()
    stack.close()
