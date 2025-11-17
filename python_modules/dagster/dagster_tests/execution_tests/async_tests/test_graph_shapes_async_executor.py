import time

import dagster as dg
from dagster._core.definitions.executor_definition import async_executor
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job


def diamond_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    async def emit() -> int:
        return 1

    @dg.op
    async def add_one(x: int) -> int:
        return x + 1

    @dg.op
    async def double(x: int) -> int:
        return x * 2

    @dg.op
    async def combine(a: int, b: int) -> int:
        return a + b

    @dg.job(executor_def=async_executor)
    def diamond_job():
        base = emit()
        combine(add_one(base), double(base))

    return diamond_job


def highly_nested_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    async def emit_one() -> int:
        return 1

    @dg.op
    async def add_one(x: int) -> int:
        time.sleep(0.01)
        return x + 1

    @dg.job(executor_def=async_executor)
    def nested_job():
        add_one.alias("add_one_outer")(
            add_one.alias("add_one_middle")(add_one.alias("add_one_inner")(emit_one()))
        )

    return nested_job


def test_diamond_job_async_executor() -> None:
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(diamond_job_def_async_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        # combine(add_one(1), double(1)) = (1 + 1) + (1 * 2) = 4
        assert result.output_for_node("combine") == 4


def test_highly_nested_job_async_executor() -> None:
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(highly_nested_job_def_async_executor),
            instance=instance,
        ) as result,
    ):
        assert result.success
        # emit_one -> 1, then three adds → 4
        assert result.output_for_node("add_one_outer") == 4
