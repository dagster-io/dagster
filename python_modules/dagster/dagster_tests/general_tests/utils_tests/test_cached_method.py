# mypy: disable-error-code=annotation-unchecked

import asyncio
import gc
import random
from collections import Counter
from collections.abc import Iterator
from itertools import cycle, repeat
from typing import NamedTuple

import objgraph
from dagster._utils.cached_method import cached_if_true_no_arg_method
from dagster_shared.utils.cached_method import (
    CACHED_METHOD_CACHE_FIELD,
    cached_method,
    get_cached_method_cache,
)


def test_cached_method() -> None:
    class MyClass:
        def __init__(self, attr1) -> None:
            self._attr1 = attr1
            self.calls = []

        @cached_method
        def my_method(self, arg1) -> tuple:
            self.calls.append(arg1)
            return (arg1, self._attr1)

    obj1 = MyClass(4)
    assert obj1.my_method(arg1="a") == ("a", 4)
    assert obj1.my_method(arg1="a") == ("a", 4)
    assert obj1.my_method(arg1="b") == ("b", 4)
    assert obj1.my_method(arg1="a") == ("a", 4)
    assert obj1.calls == ["a", "b"]

    obj2 = MyClass(5)
    assert obj2.my_method(arg1="a") == ("a", 5)
    assert obj2.my_method(arg1="b") == ("b", 5)
    assert obj2.calls == ["a", "b"]


def test_kwargs_order_irrelevant_and_no_kwargs() -> None:
    class MyClass:
        def __init__(self) -> None:
            self.calls = []

        @cached_method
        def my_method(self, arg1, arg2) -> tuple:
            self.calls.append(arg1)
            return arg1, arg2

    obj1 = MyClass()
    assert obj1.my_method(arg1="a", arg2=5) == ("a", 5)
    assert obj1.my_method(arg2=5, arg1="a") == ("a", 5)
    assert len(obj1.calls) == 1


def test_does_not_leak() -> None:
    class LeakTestKey(NamedTuple):
        attr: str

    class LeakTestValue(NamedTuple):
        attr: str

    class LeakTestObj:
        @cached_method
        def my_method(self, _arg1: LeakTestKey) -> LeakTestValue:
            return LeakTestValue("abc")

    obj = LeakTestObj()
    assert objgraph.count("LeakTestObj") == 1
    assert objgraph.count("LeakTestKey") == 0
    assert objgraph.count("LeakTestValue") == 0

    obj.my_method(_arg1=LeakTestKey("1234"))
    assert objgraph.count("LeakTestObj") == 1
    assert objgraph.count("LeakTestKey") == 1
    assert objgraph.count("LeakTestValue") == 1

    del obj
    gc.collect()
    assert objgraph.count("LeakTestObj") == 0
    assert objgraph.count("LeakTestKey") == 0
    assert objgraph.count("LeakTestValue") == 0


def test_collisions() -> None:
    class MyClass:
        @cached_method
        def stuff(self, a=None, b=None) -> dict:
            return {"a": a, "b": b}

    obj = MyClass()
    a1 = obj.stuff(a=1)
    b1 = obj.stuff(b=1)
    a2 = obj.stuff(a=2)
    b2 = obj.stuff(b=2)

    assert a1 != b1
    assert a1 != a2
    assert b1 != b2


def test_ordinal_args() -> None:
    class MyClass:
        @cached_method
        def stuff(self, a, b) -> dict:
            return {"a": a, "b": b}

    obj = MyClass()
    a1 = obj.stuff(1, None)
    b1 = obj.stuff(None, 1)
    a2 = obj.stuff(2, None)
    b2 = obj.stuff(None, 2)

    assert obj.stuff(1, None) is obj.stuff(a=1, b=None)
    assert obj.stuff(1, b=None) is obj.stuff(a=1, b=None)

    assert a1 is not b1
    assert a1 is not a2
    assert b1 is not b2


def test_scenario_documented_in_cached_method_doc_block() -> None:
    # This following example was used in the docblock to demonstrate
    # the difference with functools. In cached_method, these
    # share the same cache entry, whereas in functools.lru_cache
    # they would have three entries.
    class MyClass:
        @cached_method
        def a_method(self, arg1: str, arg2: int) -> str:
            return arg1 + str(arg2)

    obj = MyClass()
    assert obj.a_method(arg1="a", arg2=5) == "a5"
    assert obj.a_method(arg2=5, arg1="a") == "a5"
    assert obj.a_method("a", 5) == "a5"

    # only one entry
    assert len(obj.__dict__) == 1
    assert len(obj.__dict__[CACHED_METHOD_CACHE_FIELD][MyClass.a_method.__name__]) == 1


def test_async_cached_method() -> None:
    class MyClass:
        def __init__(self, attr1) -> None:
            self._attr1 = attr1
            self.calls = []

        @cached_method
        async def my_method(self, arg1) -> tuple:
            self.calls.append(arg1)
            await asyncio.sleep(0.25 * random.random())
            return (arg1, self._attr1)

    obj1 = MyClass(4)
    assert obj1.calls == []
    a_result = asyncio.run(obj1.my_method(arg1="a"))
    assert a_result == ("a", 4)
    assert obj1.calls == ["a"]
    assert asyncio.run(obj1.my_method(arg1="a")) is a_result
    b_result = asyncio.run(obj1.my_method(arg1="b"))
    assert b_result == ("b", 4)
    assert asyncio.run(obj1.my_method(arg1="a")) is a_result
    assert obj1.calls == ["a", "b"]

    async def run_my_method_a_bunch() -> list[tuple]:
        return await asyncio.gather(*[obj1.my_method(arg1="a") for i in range(100)])

    assert asyncio.run(run_my_method_a_bunch()) == [("a", 4)] * 100
    assert obj1.calls == ["a", "b"]

    obj2 = MyClass(5)
    assert asyncio.run(obj2.my_method(arg1="a")) == ("a", 5)
    assert asyncio.run(obj2.my_method(arg1="b")) == ("b", 5)
    assert obj2.calls == ["a", "b"]


def test_cached_property():
    class Bar: ...

    class Foo:
        @property
        @cached_method
        def bomp(self):
            return Bar()

    f = Foo()
    assert f.bomp is f.bomp


def test_explicit_test() -> None:
    class EnclosingClass:
        @cached_method
        def boop(self) -> int:
            return 1

    inst = EnclosingClass()

    assert get_cached_method_cache(inst, "boop") == {}

    assert inst.boop() == 1

    assert next(iter(get_cached_method_cache(inst, "boop").values())) == 1


class TestCachedIfTrueNoArgMethod:
    class MyClass:
        def __init__(self, return_values: bool | Iterator[bool] | list[bool]) -> None:
            self._return_values: Iterator[bool] = (
                return_values
                if isinstance(return_values, Iterator)
                else repeat(return_values)
                if isinstance(return_values, bool)
                else cycle(return_values)
            )
            self.call_counts: Counter[str] = Counter()

        @cached_if_true_no_arg_method
        def has_table_t1(self) -> bool:
            self.call_counts["has_table_t1"] += 1
            return next(self._return_values)

        @cached_if_true_no_arg_method
        def has_table_missing(self) -> bool:
            self.call_counts["has_table_missing"] += 1
            return False

        @cached_if_true_no_arg_method
        def has_table_exists(self) -> bool:
            self.call_counts["has_table_exists"] += 1
            return True

        def assert_call_counts(self, t1: int, missing: int = 0, exists: int = 0) -> None:
            total = t1 + missing + exists
            assert self.call_counts["has_table_t1"] == t1
            assert self.call_counts["has_table_missing"] == missing
            assert self.call_counts["has_table_exists"] == exists
            assert self.call_counts.total() == total
            assert set(self.call_counts.keys()) <= {
                "has_table_t1",
                "has_table_missing",
                "has_table_exists",
            }

    def test_cached_if_true_no_arg_method_caches_true(self) -> None:
        obj = self.MyClass(return_values=True)
        assert obj.has_table_t1() is True
        obj.assert_call_counts(1)

        assert obj.has_table_t1() is True
        obj.assert_call_counts(1)

    def test_cached_if_true_no_arg_method_does_not_cache_false(self) -> None:
        obj = self.MyClass(return_values=False)
        assert obj.has_table_t1() is False
        obj.assert_call_counts(1)

        assert obj.has_table_t1() is False
        obj.assert_call_counts(2)

    def test_cached_if_true_no_arg_method_caches_after_transition(self) -> None:
        """False results are not cached; once True is returned it is cached."""
        obj = self.MyClass(return_values=[False, False, True, False])

        assert obj.has_table_t1() is False  # call 1: False, not cached
        obj.assert_call_counts(1)

        assert obj.has_table_t1() is False  # call 2: False, not cached
        obj.assert_call_counts(2)

        assert obj.has_table_t1() is True  # call 3: True, cached
        obj.assert_call_counts(3)

        assert obj.has_table_t1() is True  # call 4: cached, not re-computed
        obj.assert_call_counts(3)

    def test_cached_if_true_no_arg_method_per_method_isolation(self) -> None:
        obj = self.MyClass(return_values=[False, True, False])
        obj.assert_call_counts(0, 0, 0)

        assert obj.has_table_t1() is False
        obj.assert_call_counts(1, 0, 0)

        assert obj.has_table_missing() is False
        obj.assert_call_counts(1, 1, 0)

        assert obj.has_table_exists() is True
        obj.assert_call_counts(1, 1, 1)

        assert obj.has_table_t1() is True
        obj.assert_call_counts(2, 1, 1)

        assert obj.has_table_missing() is False
        obj.assert_call_counts(2, 2, 1)

        assert obj.has_table_exists() is True
        obj.assert_call_counts(2, 2, 1)

        assert obj.has_table_t1() is True
        obj.assert_call_counts(2, 2, 1)

        assert obj.has_table_missing() is False
        obj.assert_call_counts(2, 3, 1)

        assert obj.has_table_exists() is True
        obj.assert_call_counts(2, 3, 1)

    def test_cached_if_true_no_arg_method_per_instance_isolation(self) -> None:
        obj_true = self.MyClass(return_values=True)
        obj_false = self.MyClass(return_values=False)

        assert obj_true.has_table_t1() is True
        obj_true.assert_call_counts(1)
        obj_false.assert_call_counts(0)

        assert obj_false.has_table_t1() is False
        obj_true.assert_call_counts(1)
        obj_false.assert_call_counts(1)

        assert obj_true.has_table_t1() is True
        obj_true.assert_call_counts(1)
        obj_false.assert_call_counts(1)

        assert obj_false.has_table_t1() is False
        obj_true.assert_call_counts(1)
        obj_false.assert_call_counts(2)

    def test_cached_if_true_no_arg_method_as_property(self) -> None:
        class MyClass:
            def __init__(self, return_value: bool) -> None:
                self._return_value = return_value
                self.call_count = 0

            @property
            @cached_if_true_no_arg_method
            def has_table_t1(self) -> bool:
                self.call_count += 1
                return self._return_value

        obj = MyClass(return_value=True)
        assert obj.has_table_t1 is True
        assert obj.call_count == 1
        assert obj.has_table_t1 is True
        assert obj.call_count == 1  # cached
