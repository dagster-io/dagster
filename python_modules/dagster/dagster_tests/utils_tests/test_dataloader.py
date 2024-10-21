import asyncio
import random
from functools import cached_property
from typing import Iterable, List, NamedTuple
from unittest import mock

import pytest
from dagster._core.loader import InstanceLoadableBy, LoadingContext
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


async def batch_load_fn(keys: List[str]):
    return [Thing(key=key, batch_keys=keys) for key in keys]


class ThingLoader(DataLoader[str, Thing]):
    def __init__(self):
        super().__init__(batch_load_fn=batch_load_fn)


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

    async def batch_load_fn(keys: List[str]):
        raise TestException()

    class Thrower(DataLoader[str, str]):
        def __init__(self):
            super().__init__(batch_load_fn=batch_load_fn)

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


class LoadableThing(
    NamedTuple("_LoadableThing", [("key", str), ("val", int)]), InstanceLoadableBy[str]
):
    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[str], context: mock.MagicMock
    ) -> List["LoadableThing"]:
        context.query(keys)
        return [LoadableThing(key, random.randint(0, 100000)) for key in keys]


class BasicLoadingContext(LoadingContext):
    def __init__(self):
        self._loaders = {}
        self._mock_instance = mock.MagicMock()

    @property
    def loaders(self):
        return self._loaders

    @property
    def instance(self) -> mock.MagicMock:
        return self._mock_instance


def test_sync_loadable_by() -> None:
    context = BasicLoadingContext()

    # test caching
    a1 = LoadableThing.blocking_get(context, "a")
    a2 = LoadableThing.blocking_get(context, "a")

    assert a1 is a2
    context.instance.query.assert_called_once_with(["a"])

    # test prepare

    LoadableThing.prepare(context, ["a", "b", "c", "d"])
    result = list(LoadableThing.blocking_get_many(context, ["b", "c"]))
    assert len(result) == 2
    b1 = result[0]
    c1 = result[1]
    # queried for b, c, and d as a batch (did not re-query a)
    context.instance.query.assert_called_with(["b", "c", "d"])

    b2 = LoadableThing.blocking_get(context, "b")
    assert b1 is b2
    c2 = LoadableThing.blocking_get(context, "c")
    assert c1 is c2

    # still just 2 calls
    assert context.instance.query.call_count == 2

    # don't need another query for d
    d1 = LoadableThing.blocking_get(context, "d")
    d2 = LoadableThing.blocking_get(context, "d")
    assert d1 == d2
    assert context.instance.query.call_count == 2
