# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import threading
import time
from collections import OrderedDict

import pytest
from dagster_celery import celery_executor

from dagster import ModeDefinition, default_executors, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunsFilter

from .utils import (
    execute_eagerly_on_celery,
    execute_on_thread,
    execute_pipeline_on_celery,
    skip_ci,
    start_celery_worker,
)

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


@pytest.mark.skip
@skip_ci
def test_priority_pipeline():
    with execute_pipeline_on_celery("priority_pipeline") as result:
        assert result.success


@pytest.mark.skip
@skip_ci
def test_eager_priority_pipeline():
    with execute_eagerly_on_celery("simple_priority_pipeline") as result:
        assert result.success
        assert list(OrderedDict.fromkeys([evt.step_key for evt in result.step_event_list])) == [
            "ten.compute",
            "nine.compute",
            "eight.compute",
            "seven_.compute",
            "six.compute",
            "five.compute",
            "four.compute",
            "three.compute",
            "two.compute",
            "one.compute",
            "zero.compute",
        ]


@skip_ci
def test_run_priority_pipeline():
    with seven.TemporaryDirectory() as tempdir:
        instance = DagsterInstance.local_temp(tempdir)

        low_done = threading.Event()
        hi_done = threading.Event()

        # enqueue low-priority tasks
        low_thread = threading.Thread(
            target=execute_on_thread,
            args=("low_pipeline", low_done),
            kwargs={"tempdir": tempdir, "tags": {"dagster-celery/run_priority": -3}},
        )
        low_thread.daemon = True
        low_thread.start()

        time.sleep(1)  # sleep so that we don't hit any sqlite concurrency issues

        # enqueue hi-priority tasks
        hi_thread = threading.Thread(
            target=execute_on_thread,
            args=("hi_pipeline", hi_done),
            kwargs={"tempdir": tempdir, "tags": {"dagster-celery/run_priority": 3}},
        )
        hi_thread.daemon = True
        hi_thread.start()

        time.sleep(5)  # sleep to give queue time to prioritize tasks

        with start_celery_worker():
            while not low_done.is_set() or not hi_done.is_set():
                time.sleep(1)

            low_runs = instance.get_runs(filters=PipelineRunsFilter(pipeline_name="low_pipeline"))
            assert len(low_runs) == 1
            low_run = low_runs[0]
            lowstats = instance.get_run_stats(low_run.run_id)
            hi_runs = instance.get_runs(filters=PipelineRunsFilter(pipeline_name="hi_pipeline"))
            assert len(hi_runs) == 1
            hi_run = hi_runs[0]
            histats = instance.get_run_stats(hi_run.run_id)

            assert lowstats.start_time < histats.start_time
            assert lowstats.end_time > histats.end_time
