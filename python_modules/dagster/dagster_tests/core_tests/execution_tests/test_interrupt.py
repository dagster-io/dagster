import time
from threading import Thread

from dagster import DagsterEventType, execute_pipeline_iterator, lambda_solid, pipeline

try:
    import _thread as thread
except ImportError:
    import thread


@lambda_solid
def sleep():
    time.sleep(0.1)


@pipeline
def sleepy():
    sleep()


def _send_kbd_int():
    time.sleep(0.05)
    thread.interrupt_main()


def test_interrupt():
    results = []
    for result in execute_pipeline_iterator(sleepy):
        results.append(result.event_type)

    assert DagsterEventType.PIPELINE_SUCCESS in results

    results = []
    Thread(target=_send_kbd_int).start()

    try:
        for result in execute_pipeline_iterator(sleepy):
            results.append(result.event_type)
    except KeyboardInterrupt:
        pass

    assert DagsterEventType.STEP_FAILURE in results
    assert DagsterEventType.PIPELINE_FAILURE in results
