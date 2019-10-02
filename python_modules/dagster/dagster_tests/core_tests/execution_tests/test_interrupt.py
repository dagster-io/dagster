import os
import time
from threading import Thread

from dagster import DagsterEventType, execute_pipeline_iterator, lambda_solid, pipeline
from dagster.utils import safe_tempfile_path

try:
    import _thread as thread
except ImportError:
    import thread


def _send_kbd_int(temp_file):
    while not os.path.exists(temp_file):
        time.sleep(0.1)

    thread.interrupt_main()


def test_interrupt():
    with safe_tempfile_path() as success_tempfile:

        @lambda_solid
        def write_a_file():
            with open(success_tempfile, 'w') as ff:
                ff.write('yup')

            while True:
                time.sleep(0.1)

        @pipeline
        def write_a_file_pipeline():
            write_a_file()

        # launch a thread the waits until the file is written to launch an interrupt
        Thread(target=_send_kbd_int, args=(success_tempfile,)).start()

        results = []
        try:
            # launch a pipeline that writes a file and loops infinitely
            # next time the launched thread wakes up it will send a keyboard
            # interrupt
            for result in execute_pipeline_iterator(write_a_file_pipeline):
                results.append(result.event_type)
            assert False  # should never reach
        except KeyboardInterrupt:
            pass

        assert DagsterEventType.STEP_FAILURE in results
        assert DagsterEventType.PIPELINE_FAILURE in results
