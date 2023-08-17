from inspect import Parameter, signature
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

    dagster_internal_init_params = signature(cls.dagster_internal_init).parameters
    init_params = signature(cls.__init__).parameters
    dagster_internal_init_return = signature(cls.dagster_internal_init).return_annotation

    assert (
        dagster_internal_init_return == cls or dagster_internal_init_return == cls.__name__
    ), f"{cls.__name__}.dagster_internal_init has a different return type than the class itself"

    assert all(p.default == Parameter.empty for p in dagster_internal_init_params.values()), (
        f"{cls.__name__}.dagster_internal_init has one or more default values,"
        " dagster_internal_init methods cannot have default values"
    )

    assert all(p.kind == Parameter.KEYWORD_ONLY for p in dagster_internal_init_params.values()), (
        f"{cls.__name__}.dagster_internal_init has one or more positional arguments,"
        " dagster_internal_init methods can only have keyword-only arguments"
    )

    assert [*dagster_internal_init_params.keys()] == (
        [k for k in init_params.keys() if k != "self"]
    ), f"{cls.__name__}.dagster_internal_init has different arguments than __init__"
