from dataclasses import FrozenInstanceError

import pytest
from dagster._core.utils import strict_dataclass
from pydantic import ValidationError


def test_kwargs():
    @strict_dataclass()
    class MyClass:
        a: int
        b: str

    foo = MyClass(a=5, b="x")
    assert foo.a == 5
    assert foo.b == "x"


def test_kwargs_extras():
    @strict_dataclass()
    class MyClass:
        a: int
        b: str

    with pytest.raises(ValidationError):
        MyClass(a=5, b="x", c=5)


def test_frozen():
    @strict_dataclass()
    class MyClass:
        a: int
        b: str

    foo = MyClass(a=5, b="x")

    with pytest.raises(FrozenInstanceError):
        foo.a = 6


def test_positional_args_default():
    @strict_dataclass()
    class MyClass:
        a: int
        b: str

    with pytest.raises(TypeError):
        MyClass(5, "x")


def test_positional_args_override_init():
    @strict_dataclass(positional_args={"a"})
    class MyClass:
        a: int
        b: str

    foo = MyClass(5, b="x")
    assert foo.a == 5
    assert foo.b == "x"

    with pytest.raises(TypeError):
        MyClass(5, "x")


def test_type_validation():
    @strict_dataclass()
    class MyClass:
        a: int
        b: str

    with pytest.raises(ValidationError):
        MyClass(a=5, b=6)


def test_too_many_positional_arguments():
    @strict_dataclass(positional_args={"a"})
    class MyClass:
        a: int

    with pytest.raises(TypeError):
        MyClass(5, 6)


def test_inheritance():
    @strict_dataclass()
    class MyClass:
        a: int

    @strict_dataclass()
    class MySubClass(MyClass):
        b: str

    foo = MySubClass(a=5, b="x")
    assert foo.a == 5
    assert foo.b == "x"
