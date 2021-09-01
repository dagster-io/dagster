import asyncio

from dagster import Output, execute_solid, solid


def test_aio_solid():
    @solid
    async def aio_solid(_):
        await asyncio.sleep(0.01)
        return "done"

    result = execute_solid(aio_solid)
    assert result.output_value() == "done"


def test_aio_gen_solid():
    @solid
    async def aio_gen(_):
        await asyncio.sleep(0.01)
        yield Output("done")

    result = execute_solid(aio_gen)
    assert result.output_value() == "done"
