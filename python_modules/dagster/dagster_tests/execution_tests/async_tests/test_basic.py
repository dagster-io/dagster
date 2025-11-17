import time

import anyio
import dagster as dg
from dagster._core.definitions.executor_definition import async_executor
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job


def sync_job_def_in_process_executor() -> dg.JobDefinition:
    @dg.op
    def emit_one():
        return 1

    @dg.op()
    def slow_add_one(x: int):
        time.sleep(0.01)
        return x + 1

    @dg.op
    def slow_double(x: int):
        time.sleep(0.01)
        return x * 2

    @dg.job(executor_def=dg.in_process_executor)
    def sync_job():
        slow_double(slow_add_one(emit_one()))

    return sync_job


def sync_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    def emit_one():
        return 1

    @dg.op()
    def slow_add_one(x: int):
        time.sleep(0.01)
        return x + 1

    @dg.op
    def slow_double(x: int):
        time.sleep(0.01)
        return x * 2

    @dg.job(executor_def=async_executor)
    def sync_job():
        slow_double(slow_add_one(emit_one()))

    return sync_job


def async_job_def_in_process_executor() -> dg.JobDefinition:
    @dg.op
    async def emit_one():
        return 1

    @dg.op()
    async def slow_add_one(x: int = 1) -> int:
        await anyio.sleep(0.01)
        return x + 1

    @dg.op
    async def slow_double(x: int) -> int:
        await anyio.sleep(0.01)
        return x * 2

    @dg.job(
        executor_def=dg.in_process_executor,
    )
    def async_job():
        slow_double(slow_add_one(emit_one()))

    return async_job


def async_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    async def emit_one():
        return 1

    @dg.op()
    async def slow_add_one(x: int = 1) -> int:
        await anyio.sleep(0.01)
        return x + 1

    @dg.op
    async def slow_double(x: int) -> int:
        await anyio.sleep(0.01)
        return x * 2

    @dg.job(
        executor_def=async_executor,
    )
    def async_job():
        slow_double(slow_add_one(emit_one()))

    return async_job


def test_sync_job_in_process_executor():
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(sync_job_def_in_process_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.output_for_node("slow_double") == 4


def test_sync_job_async_executor():
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(sync_job_def_async_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.output_for_node("slow_double") == 4


def test_async_job_in_process_executor():
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(async_job_def_in_process_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.output_for_node("slow_double") == 4


def test_async_job_async_executor():
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(async_job_def_async_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.output_for_node("slow_double") == 4
