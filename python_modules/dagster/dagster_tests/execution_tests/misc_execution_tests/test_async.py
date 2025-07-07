import asyncio
from contextlib import asynccontextmanager

import dagster as dg
import pytest
from dagster._utils.test import wrap_op_in_graph_and_execute
from pydantic import PrivateAttr


def test_aio_op():
    @dg.op
    async def aio_op(_):
        await asyncio.sleep(0.01)
        return "done"

    result = wrap_op_in_graph_and_execute(aio_op)
    assert result.output_value() == "done"


def test_aio_asset():
    @dg.asset
    async def aio_asset(_):
        await asyncio.sleep(0.01)
        return dg.Output("done")

    result = dg.materialize([aio_asset])
    assert result.success


def test_aio_gen_op():
    @dg.op
    async def aio_gen(_):
        await asyncio.sleep(0.01)
        yield dg.Output("done")

    result = wrap_op_in_graph_and_execute(aio_gen)
    assert result.output_value() == "done"


def test_can_run_in_async():
    @dg.op
    def emit():
        return 1

    async def _go():
        result = wrap_op_in_graph_and_execute(emit)
        assert result.output_value() == 1

    asyncio.run(_go())


def test_aio_resource():
    class AioResource(dg.ConfigurableResource):
        _loop = PrivateAttr()

        @property
        def loop(self):
            return self._loop

        @asynccontextmanager
        async def yield_for_execution(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            await asyncio.sleep(0)
            self._loop = asyncio.get_running_loop()
            yield self

    @dg.op
    async def aio_op(aio_resource: AioResource):
        await asyncio.sleep(0)
        assert aio_resource.loop is asyncio.get_running_loop()
        return "done"

    result = wrap_op_in_graph_and_execute(aio_op, {"aio_resource": AioResource()})
    assert result.output_value() == "done"

    with pytest.raises(
        dg.DagsterError, match="Unable to handle resource with async def yield_for_execution"
    ):
        dg.build_op_context({"aio_resource": AioResource()})

    loop = asyncio.new_event_loop()
    with dg.build_op_context({"aio_resource": AioResource()}, event_loop=loop) as ctx:
        assert loop.run_until_complete(aio_op(ctx)) == "done"

    @dg.asset
    async def aio_asset(aio_resource: AioResource):
        await asyncio.sleep(0)
        assert aio_resource.loop is asyncio.get_running_loop()
        return "done"

    result = dg.materialize([aio_asset], resources={"aio_resource": AioResource()})
    assert result.output_for_node("aio_asset") == "done"

    with pytest.raises(
        dg.DagsterError, match="Unable to handle resource with async def yield_for_execution"
    ):
        dg.build_op_context({"aio_resource": AioResource()})

    loop = asyncio.new_event_loop()
    with dg.build_asset_context({"aio_resource": AioResource()}, event_loop=loop) as ctx:
        assert loop.run_until_complete(aio_asset(ctx)) == "done"  # type: ignore
