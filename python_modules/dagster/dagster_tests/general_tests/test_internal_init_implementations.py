import inspect
from typing import Type

import dagster as dagster
import pytest
from dagster._utils import IHasInternalInit

INTERNAL_INIT_SUBCLASSES = [
    symbol
    for symbol in dagster.__dict__.values()
    if isinstance(symbol, type)
    and issubclass(symbol, IHasInternalInit)
    and IHasInternalInit
    in symbol.__bases__  # ensure that the class is a direct subclass of IHasInternalInit (not a subclass of a subclass)
]


@pytest.mark.parametrize("cls", INTERNAL_INIT_SUBCLASSES)
def test_dagster_internal_init_class_follow_rules(cls: Type):
    assert hasattr(
        cls, "dagster_internal_init"
    ), f"{cls.__name__} does not have dagster_internal_init method"

    dagster_internal_init_argspec = inspect.getfullargspec(cls.dagster_internal_init)
    init_args_spec = inspect.getfullargspec(cls.__init__)

    dagster_internal_init_return = inspect.signature(cls.dagster_internal_init).return_annotation

    assert (
        dagster_internal_init_return == cls or dagster_internal_init_return == cls.__name__
    ), f"{cls.__name__}.dagster_internal_init has a different return type than the class itself"

    assert dagster_internal_init_argspec.defaults is None, (
        f"{cls.__name__}.dagster_internal_init has one or more default values,"
        " dagster_internal_init methods cannot have default values"
    )

    assert dagster_internal_init_argspec.args == [], (
        f"{cls.__name__}.dagster_internal_init has one or more positional arguments,"
        " dagster_internal_init methods can only have keyword-only arguments"
    )

    assert dagster_internal_init_argspec.kwonlyargs == (
        init_args_spec.args[1:] + init_args_spec.kwonlyargs  # exclude self
    ), f"{cls.__name__}.dagster_internal_init has different arguments than __init__"
