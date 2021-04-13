import asyncio
import tempfile
import time
from threading import Thread

import dagster_pandas as dagster_pd
import pytest
from dagster import (
    DagsterUnmetExecutorRequirementsError,
    InputDefinition,
    ModeDefinition,
    execute_pipeline,
    execute_pipeline_iterator,
    file_relative_path,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.definitions.executor import default_executors
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.events import DagsterEventType
from dagster.core.test_utils import (
    instance_for_test,
    instance_for_test_tempdir,
    nesting_composite_pipeline,
)
from dagster.utils import send_interrupt
from dagster_dask import DataFrame, dask_executor
from dask.distributed import Scheduler, Worker


@solid
def simple(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def dask_engine_pipeline():
    simple()


def test_execute_on_dask_local():
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test_tempdir(tempdir) as instance:
            result = execute_pipeline(
                reconstructable(dask_engine_pipeline),
                run_config={
                    "intermediate_storage": {"filesystem": {"config": {"base_dir": tempdir}}},
                    "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
                },
                instance=instance,
            )
            assert result.result_for_solid("simple").output_value() == 1


def dask_composite_pipeline():
    return nesting_composite_pipeline(
        6, 2, mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])]
    )


def test_composite_execute():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(dask_composite_pipeline),
            run_config={
                "intermediate_storage": {"filesystem": {}},
                "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
            },
            instance=instance,
        )
        assert result.success


@solid(input_defs=[InputDefinition("df", dagster_pd.DataFrame)])
def pandas_solid(_, df):  # pylint: disable=unused-argument
    pass


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def pandas_pipeline():
    pandas_solid()


def test_pandas_dask():
    run_config = {
        "solids": {
            "pandas_solid": {
                "inputs": {"df": {"csv": {"path": file_relative_path(__file__, "ex.csv")}}}
            }
        }
    }

    with instance_for_test() as instance:
        result = execute_pipeline(
            ReconstructablePipeline.for_file(__file__, pandas_pipeline.name),
            run_config={
                "intermediate_storage": {"filesystem": {}},
                "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
                **run_config,
            },
            instance=instance,
        )

        assert result.success


@solid(input_defs=[InputDefinition("df", DataFrame)])
def dask_solid(_, df):  # pylint: disable=unused-argument
    pass


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def dask_pipeline():
    dask_solid()


def test_dask():
    run_config = {
        "solids": {
            "dask_solid": {
                "inputs": {
                    "df": {"read": {"csv": {"path": file_relative_path(__file__, "ex*.csv")}}}
                }
            }
        }
    }
    with instance_for_test() as instance:

        result = execute_pipeline(
            ReconstructablePipeline.for_file(__file__, dask_pipeline.name),
            run_config={
                "intermediate_storage": {"filesystem": {}},
                "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
                **run_config,
            },
            instance=instance,
        )

    assert result.success


def test_execute_on_dask_local_with_intermediate_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test_tempdir(tempdir) as instance:
            result = execute_pipeline(
                reconstructable(dask_engine_pipeline),
                run_config={
                    "intermediate_storage": {"filesystem": {"config": {"base_dir": tempdir}}},
                    "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
                },
                instance=instance,
            )
            assert result.result_for_solid("simple").output_value() == 1


def test_execute_on_dask_local_with_default_storage():
    with pytest.raises(DagsterUnmetExecutorRequirementsError):
        with instance_for_test() as instance:
            result = execute_pipeline(
                reconstructable(dask_engine_pipeline),
                run_config={
                    "execution": {"dask": {"config": {"cluster": {"local": {"timeout": 30}}}}},
                },
                instance=instance,
            )
            assert result.result_for_solid("simple").output_value() == 1


@solid(input_defs=[InputDefinition("df", DataFrame)])
def sleepy_dask_solid(_, df):  # pylint: disable=unused-argument
    start_time = time.time()
    while True:
        time.sleep(0.1)
        if time.time() - start_time > 120:
            raise Exception("Timed out")


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def sleepy_dask_pipeline():
    sleepy_dask_solid()


def test_dask_terminate():
    run_config = {
        "solids": {
            "sleepy_dask_solid": {
                "inputs": {
                    "df": {"read": {"csv": {"path": file_relative_path(__file__, "ex*.csv")}}}
                }
            }
        }
    }

    interrupt_thread = None
    result_types = []

    with instance_for_test() as instance:
        for result in execute_pipeline_iterator(
            pipeline=ReconstructablePipeline.for_file(__file__, sleepy_dask_pipeline.name),
            run_config=run_config,
            instance=instance,
        ):
            # Interrupt once the first step starts
            if result.event_type == DagsterEventType.STEP_START and not interrupt_thread:
                interrupt_thread = Thread(target=send_interrupt, args=())
                interrupt_thread.start()

            if result.event_type == DagsterEventType.STEP_FAILURE:
                assert (
                    "DagsterExecutionInterruptedError" in result.event_specific_data.error.message
                )

            result_types.append(result.event_type)

        interrupt_thread.join()

        assert DagsterEventType.STEP_FAILURE in result_types
        assert DagsterEventType.PIPELINE_FAILURE in result_types


def test_existing_scheduler():
    def _execute(scheduler_address, instance):
        return execute_pipeline(
            reconstructable(dask_engine_pipeline),
            run_config={
                "intermediate_storage": {"filesystem": {}},
                "execution": {
                    "dask": {"config": {"cluster": {"existing": {"address": scheduler_address}}}}
                },
            },
            instance=instance,
        )

    async def _run_test():
        with instance_for_test() as instance:
            async with Scheduler() as scheduler:
                async with Worker(scheduler.address) as _:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, _execute, scheduler.address, instance
                    )
                    assert result.success
                    assert result.result_for_solid("simple").output_value() == 1

    asyncio.get_event_loop().run_until_complete(_run_test())
