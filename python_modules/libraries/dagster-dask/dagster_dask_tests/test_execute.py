import asyncio
import tempfile
import time
from threading import Thread

import dagster_pandas as dagster_pd
import pytest
from dagster import (
    VersionStrategy,
    file_relative_path,
    job,
    op,
    reconstructable,
)
from dagster._core.definitions.input import In
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import execute_job, execute_run_iterator
from dagster._core.test_utils import instance_for_test, nesting_graph
from dagster._utils import send_interrupt
from dagster_dask import DataFrame, dask_executor
from dask.distributed import Scheduler, Worker


@op
def simple(_):
    return 1


def dask_engine_job() -> JobDefinition:
    @job(
        executor_def=dask_executor,
    )
    def job_def():
        simple()

    return job_def


def test_execute_on_dask_local():
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test(temp_dir=tempdir) as instance:
            with execute_job(
                reconstructable(dask_engine_job),
                run_config={
                    "resources": {"io_manager": {"config": {"base_dir": tempdir}}},
                    "execution": {"config": {"cluster": {"local": {"timeout": 30}}}},
                },
                instance=instance,
            ) as result:
                assert result.output_for_node("simple") == 1


def dask_nested_graph_job():
    return nesting_graph(
        6,
        2,
    ).to_job(executor_def=dask_executor)


def test_composite_execute():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(dask_nested_graph_job),
            run_config={
                "execution": {"config": {"cluster": {"local": {"timeout": 30}}}},
            },
            instance=instance,
        ) as result:
            assert result.success


@op(ins={"df": In(dagster_pd.DataFrame)})
def pandas_op(_, df):
    pass


def pandas_job() -> JobDefinition:
    @job(
        executor_def=dask_executor,
    )
    def job_def():
        pandas_op()

    return job_def


def test_pandas_dask():
    run_config = {
        "ops": {
            "pandas_op": {
                "inputs": {"df": {"csv": {"path": file_relative_path(__file__, "ex.csv")}}}
            }
        }
    }

    with instance_for_test() as instance:
        with execute_job(
            reconstructable(pandas_job),
            run_config={
                "execution": {"config": {"cluster": {"local": {"timeout": 30}}}},
                **run_config,
            },
            instance=instance,
        ) as result:
            assert result.success


@op(ins={"df": In(DataFrame)})
def dask_op(_, df):
    pass


def dask_job() -> JobDefinition:
    @job(
        executor_def=dask_executor,
    )
    def job_def():
        dask_op()

    return job_def


def test_dask():
    run_config = {
        "ops": {
            "dask_op": {
                "inputs": {
                    "df": {"read": {"csv": {"path": file_relative_path(__file__, "ex*.csv")}}}
                }
            }
        }
    }
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(dask_job),
            run_config={
                "execution": {"config": {"cluster": {"local": {"timeout": 30}}}},
                **run_config,
            },
            instance=instance,
        ) as result:
            assert result.success


@op(ins={"df": In(DataFrame)})
def sleepy_dask_op(_, df):
    start_time = time.time()
    while True:
        time.sleep(0.1)
        if time.time() - start_time > 120:
            raise Exception("Timed out")


def sleepy_dask_job() -> JobDefinition:
    @job(
        executor_def=dask_executor,
    )
    def job_def():
        sleepy_dask_op()

    return job_def


@pytest.mark.skip(
    """
    Fails because 'DagsterExecutionInterruptedError' is not actually raised-- there's a timeout
    instead. It's not clear that the test ever was working-- prior to conversion to op/job/graph
    APIs, it appears to have been mistakenly not using the dask executor. 
    """
)
def test_dask_terminate():
    run_config = {
        "execution": {"config": {"cluster": {"local": {"timeout": 30}}}},
        "ops": {
            "sleepy_dask_op": {
                "inputs": {
                    "df": {"read": {"csv": {"path": file_relative_path(__file__, "ex*.csv")}}}
                }
            }
        },
    }

    interrupt_thread = None
    result_types = []

    with instance_for_test() as instance:
        dagster_run = instance.create_run_for_job(
            sleepy_dask_job(),
            run_config=run_config,
        )

        for event in execute_run_iterator(
            i_job=reconstructable(sleepy_dask_job),
            dagster_run=dagster_run,
            instance=instance,
        ):
            # Interrupt once the first step starts
            if event.event_type == DagsterEventType.STEP_START and not interrupt_thread:
                interrupt_thread = Thread(target=send_interrupt, args=())
                interrupt_thread.start()

            if event.event_type == DagsterEventType.STEP_FAILURE:
                assert "DagsterExecutionInterruptedError" in event.event_specific_data.error.message

            result_types.append(event.event_type)

        assert interrupt_thread
        interrupt_thread.join()

        assert DagsterEventType.STEP_FAILURE in result_types
        assert DagsterEventType.PIPELINE_FAILURE in result_types


@pytest.mark.skip(
    "Failing with RuntimeError: This event loop is already running since distributed==2022.1.0"
)
def test_existing_scheduler():
    def _execute(scheduler_address, instance):
        with execute_job(
            reconstructable(dask_engine_job),
            run_config={
                "execution": {"config": {"cluster": {"existing": {"address": scheduler_address}}}},
            },
            instance=instance,
        ) as result:
            return result

    async def _run_test():
        with instance_for_test() as instance:
            async with Scheduler() as scheduler:
                async with Worker(scheduler.address) as _:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, _execute, scheduler.address, instance
                    )
                    assert result.success
                    assert result.output_for_node("simple") == 1

    asyncio.get_event_loop().run_until_complete(_run_test())


@op
def foo_op():
    return "foo"


class BasicVersionStrategy(VersionStrategy):
    def get_op_version(self, _):
        return "foo"


def foo_job() -> JobDefinition:
    @job(
        executor_def=dask_executor,
        version_strategy=BasicVersionStrategy(),
    )
    def job_def():
        foo_op()

    return job_def


def test_dask_executor_memoization():
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(foo_job),
            instance=instance,
            run_config={"execution": {"config": {"cluster": {"local": {"timeout": 30}}}}},
        ) as result:
            assert result.success
            assert result.output_for_node("foo_op") == "foo"

        with execute_job(
            reconstructable(foo_job),
            instance=instance,
            run_config={"execution": {"config": {"cluster": {"local": {"timeout": 30}}}}},
        ) as result:
            assert result.success
            assert len(result.all_node_events) == 0
