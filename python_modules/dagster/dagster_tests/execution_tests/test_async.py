import asyncio

from dagster import In, Out, op, Output
from dagster._legacy import execute_solid, solid


def test_aio_solid():
    @op
    async def aio_op(_):
        await asyncio.sleep(0.01)
        return "done"

    result = execute_solid(aio_op)
    assert result.output_value() == "done"


def test_aio_gen_solid():
    @op
    async def aio_gen(_):
        await asyncio.sleep(0.01)
        yield Output("done")

    result = execute_solid(aio_gen)
    assert result.output_value() == "done"
