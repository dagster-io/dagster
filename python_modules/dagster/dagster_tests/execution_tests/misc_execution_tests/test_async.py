import asyncio

from dagster import Output, asset, materialize
from dagster._core.definitions.decorators import op
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_aio_op():
    @op
    async def aio_op(_):
        await asyncio.sleep(0.01)
        return "done"

    result = wrap_op_in_graph_and_execute(aio_op)
    assert result.output_value() == "done"


def test_aio_asset():
    @asset
    async def aio_asset(_):
        await asyncio.sleep(0.01)
        return Output("done")

    result = materialize([aio_asset])
    assert result.success


def test_aio_gen_op():
    @op
    async def aio_gen(_):
        await asyncio.sleep(0.01)
        yield Output("done")

    result = wrap_op_in_graph_and_execute(aio_gen)
    assert result.output_value() == "done"
