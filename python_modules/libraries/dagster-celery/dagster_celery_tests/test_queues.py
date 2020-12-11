import threading
import time

from dagster import ModeDefinition, default_executors
from dagster.core.test_utils import instance_for_test
from dagster_celery import celery_executor

from .utils import execute_on_thread, start_celery_worker

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


def test_multiqueue(rabbitmq):  # pylint: disable=unused-argument
    with instance_for_test() as instance:

        done = threading.Event()
        with start_celery_worker():
            execute_thread = threading.Thread(
                target=execute_on_thread, args=("multiqueue_pipeline", done, instance.get_ref())
            )
            execute_thread.daemon = True
            execute_thread.start()
            time.sleep(1)
            assert not done.is_set()
            with start_celery_worker(queue="fooqueue"):
                execute_thread.join()
                assert done.is_set()
