# pylint doesn't know about pytest fixtures

import tempfile
import threading
import time
from collections import OrderedDict

from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.test_utils import instance_for_test
from dagster_celery.tags import DAGSTER_CELERY_RUN_PRIORITY_TAG

from dagster_celery_tests.utils import (
    execute_eagerly_on_celery,
    execute_on_thread,
    start_celery_worker,
)


def test_eager_priority_job():
    with execute_eagerly_on_celery("simple_priority_job") as result:
        assert result.success
        step_events_in_order = [event for event in result.all_events if event.is_step_event]
        assert list(OrderedDict.fromkeys([evt.step_key for evt in step_events_in_order])) == [
            "ten",
            "nine",
            "eight",
            "seven_",
            "six",
            "five",
            "four",
            "three",
            "two",
            "one",
            "zero",
        ]


def test_run_priority_job(rabbitmq):
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test(temp_dir=tempdir) as instance:
            low_done = threading.Event()
            hi_done = threading.Event()

            # enqueue low-priority tasks
            low_thread = threading.Thread(
                target=execute_on_thread,
                args=("low_job", low_done, instance.get_ref()),
                kwargs={
                    "tempdir": tempdir,
                    "tags": {DAGSTER_CELERY_RUN_PRIORITY_TAG: "-3"},
                },
                daemon=True,
            )
            low_thread.start()

            time.sleep(1)  # sleep so that we don't hit any sqlite concurrency issues

            # enqueue hi-priority tasks
            hi_thread = threading.Thread(
                target=execute_on_thread,
                args=("hi_job", hi_done, instance.get_ref()),
                kwargs={
                    "tempdir": tempdir,
                    "tags": {DAGSTER_CELERY_RUN_PRIORITY_TAG: "3"},
                },
                daemon=True,
            )
            hi_thread.start()

            time.sleep(5)  # sleep to give queue time to prioritize tasks

            with start_celery_worker():
                while not low_done.is_set() or not hi_done.is_set():
                    time.sleep(1)

                low_runs = instance.get_runs(filters=RunsFilter(job_name="low_job"))
                assert len(low_runs) == 1
                low_run = low_runs[0]
                lowstats = instance.get_run_stats(low_run.run_id)
                hi_runs = instance.get_runs(filters=RunsFilter(job_name="hi_job"))
                assert len(hi_runs) == 1
                hi_run = hi_runs[0]
                histats = instance.get_run_stats(hi_run.run_id)

                assert lowstats.start_time < histats.start_time
