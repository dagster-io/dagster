import pytest
from dagster._model import DagsterModel
from pydantic import ValidationError


def test_override_constructor_in_subclass():
    class MyClass(DagsterModel):
        foo: str
        bar: int

        def __init__(self, foo: str, bar: int):
            super().__init__(foo=foo, bar=bar)

    MyClass(foo="fdsjk", bar=4)


def test_override_constructor_in_subclass_different_arg_names():
    class MyClass(DagsterModel):
        foo: str
        bar: int

        def __init__(self, fooarg: str, bararg: int):
            super().__init__(foo=fooarg, bar=bararg)

    MyClass(fooarg="fdsjk", bararg=4)


def test_override_constructor_in_subclass_wrong_type():
    class MyClass(DagsterModel):
        foo: str
        bar: int

        def __init__(self, foo: str, bar: str):
            super().__init__(foo=foo, bar=bar)

    with pytest.raises(ValidationError):
        MyClass(foo="fdsjk", bar="fdslk")
