# mypy: disable-error-code=annotation-unchecked

import gc
from typing import NamedTuple

import objgraph
import pytest
from dagster._check import CheckError
from dagster._utils.cached_method import cached_method


def test_cached_method():
    class MyClass:
        def __init__(self, attr1):
            self._attr1 = attr1
            self.calls = []

        @cached_method
        def my_method(self, arg1):
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


def test_kwargs_order_irrelevant_and_no_kwargs():
    class MyClass:
        def __init__(self):
            self.calls = []

        @cached_method
        def my_method(self, arg1, arg2):
            self.calls.append(arg1)
            return arg1, arg2

    obj1 = MyClass()
    assert obj1.my_method(arg1="a", arg2=5) == ("a", 5)
    assert obj1.my_method(arg2=5, arg1="a") == ("a", 5)
    assert len(obj1.calls) == 1

    with pytest.raises(CheckError, match="does not support non-keyword arguments"):
        obj1.my_method("a", 5)


def test_does_not_leak():
    class KeyClass(NamedTuple):
        attr: str

    class ValueClass(NamedTuple):
        attr: str

    class MyClass:
        @cached_method
        def my_method(self, _arg1: KeyClass) -> ValueClass:
            return ValueClass("abc")

    obj = MyClass()
    assert objgraph.count("MyClass") == 1
    assert objgraph.count("KeyClass") == 0
    assert objgraph.count("ValueClass") == 0

    obj.my_method(_arg1=KeyClass("1234"))
    assert objgraph.count("MyClass") == 1
    assert objgraph.count("KeyClass") == 1
    assert objgraph.count("ValueClass") == 1

    del obj
    gc.collect()
    assert objgraph.count("MyClass") == 0
    assert objgraph.count("KeyClass") == 0
    assert objgraph.count("ValueClass") == 0


def test_collisions():
    class MyClass:
        @cached_method
        def stuff(self, a=None, b=None):
            return {"a": a, "b": b}

    obj = MyClass()
    a1 = obj.stuff(a=1)
    b1 = obj.stuff(b=1)
    a2 = obj.stuff(a=2)
    b2 = obj.stuff(b=2)

    assert a1 != b1
    assert a1 != a2
    assert b1 != b2
