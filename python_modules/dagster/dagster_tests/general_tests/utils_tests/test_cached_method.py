# mypy: disable-error-code=annotation-unchecked

import gc
from typing import Dict, NamedTuple, Tuple

import objgraph
from dagster._utils.cached_method import cached_method


def test_cached_method() -> None:
    class MyClass:
        def __init__(self, attr1) -> None:
            self._attr1 = attr1
            self.calls = []

        @cached_method
        def my_method(self, arg1) -> Tuple:
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
        def my_method(self, arg1, arg2) -> Tuple:
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
        def stuff(self, a=None, b=None) -> Dict:
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
        def stuff(self, a, b) -> Dict:
            return {"a": a, "b": b}

    obj = MyClass()
    a1 = obj.stuff(1, None)
    b1 = obj.stuff(None, 1)
    a2 = obj.stuff(2, None)
    b2 = obj.stuff(None, 2)

    assert a1 != b1
    assert a1 != a2
    assert b1 != b2


def test_doc_string_scenario_canonicalized_cache_entry() -> None:
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
