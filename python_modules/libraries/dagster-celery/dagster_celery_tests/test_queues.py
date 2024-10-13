import threading
import time

from dagster._core.test_utils import instance_for_test

from dagster_celery_tests.utils import execute_on_thread, start_celery_worker


def test_multiqueue(rabbitmq):
    with instance_for_test() as instance:
        done = threading.Event()
        with start_celery_worker():
            execute_thread = threading.Thread(
                target=execute_on_thread,
                args=("multiqueue_job", done, instance.get_ref()),
                daemon=True,
            )
            execute_thread.start()
            time.sleep(1)
            assert not done.is_set()
            with start_celery_worker(queue="fooqueue"):
                execute_thread.join()
                assert done.is_set()
