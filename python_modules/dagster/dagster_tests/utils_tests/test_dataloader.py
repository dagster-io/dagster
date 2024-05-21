import asyncio
from functools import cached_property
from typing import List

import pytest
from dagster._model import DagsterModel
from dagster._utils.aiodataloader import DataLoader


class Context:
    @cached_property
    def loader(self) -> "ThingLoader":
        return ThingLoader()


class Thing(DagsterModel):
    key: str
    batch_keys: List[str]

    @staticmethod
    async def gen(context: Context, key: str) -> "Thing":
        return await context.loader.load(key)

    async def gen_other_thing(self, context: Context):
        return await context.loader.load(f"{self.key}_other")

    async def gen_other_other_other_thing(self, context: Context):
        other = await self.gen_other_thing(context)
        other_other = await other.gen_other_thing(context)
        return await other_other.gen_other_thing(context)


class ThingLoader(DataLoader[str, Thing]):
    async def batch_load_fn(self, keys: List[str]):
        return [Thing(key=key, batch_keys=keys) for key in keys]


def test_basic() -> None:
    async def two_round_trips(loader: ThingLoader, key: str):
        thing = await loader.load(key)
        repeat = await loader.load(thing.key)
        # test caching
        assert repeat is thing
        return thing

    async def main() -> None:
        loader = ThingLoader()

        thing1, thing2, thing3 = await asyncio.gather(
            two_round_trips(loader, "key_0"),
            two_round_trips(loader, "key_1"),
            two_round_trips(loader, "key_2"),
        )
        keys = ["key_0", "key_1", "key_2"]

        # test batching
        assert thing1.batch_keys == keys
        assert thing2.batch_keys == keys
        assert thing3.batch_keys == keys

    asyncio.run(main())


def test_event_loop_change() -> None:
    loader_cache = {}

    async def _load_memoized(k):
        if "thing" not in loader_cache:
            loader_cache["thing"] = ThingLoader()
        return await loader_cache["thing"].load(k)

    # first one is fine
    result = asyncio.run(_load_memoized("test_m"))
    assert result.key

    # second throws
    with pytest.raises(Exception, match="event loop has changed"):
        _ = asyncio.run(_load_memoized("test_m_2"))


def test_exception() -> None:
    class TestException(Exception): ...

    class Thrower(DataLoader[str, str]):
        async def batch_load_fn(self, keys: List[str]):
            raise TestException()

    async def _test():
        loader = Thrower()
        with pytest.raises(TestException):
            _ = await loader.load("foo")

    asyncio.run(_test())


def test_deep_tree():
    async def _fetch(context: Context, key: str):
        thing = await Thing.gen(context, key)
        return await thing.gen_other_other_other_thing(ctx)

    async def _test(context):
        return await asyncio.gather(
            _fetch(context, "one"),
            _fetch(context, "two"),
        )

    ctx = Context()

    one, two = asyncio.run(_test(ctx))
    assert one.batch_keys == two.batch_keys
    assert one.batch_keys == ["one_other_other_other", "two_other_other_other"]


def test_bad_load_fn():
    async def _oops(wrong, args, here): ...

    async def _test():
        loader = DataLoader(_oops)
        done, pending = await asyncio.wait(
            (loader.load(1),),
            timeout=0.01,
        )
        assert not pending
        assert len(done) == 1

        with pytest.raises(TypeError):
            done[0].result()

    asyncio.run(_test())
