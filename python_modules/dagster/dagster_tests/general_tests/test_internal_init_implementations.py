import inspect
from typing import Type

import pytest
from dagster._utils import IHasInternalInit


@pytest.mark.parametrize("cls", IHasInternalInit.__subclasses__())
def test_internal_init_class_follow_rules(cls: Type):
    assert hasattr(cls, "internal_init"), f"{cls.__name__} does not have internal_init method"

    internal_init_argspec = inspect.getfullargspec(cls.internal_init)
    init_args_spec = inspect.getfullargspec(cls.__init__)

    internal_init_return = inspect.signature(cls.internal_init).return_annotation

    assert (
        internal_init_return == cls or internal_init_return == cls.__name__
    ), f"{cls.__name__}.internal_init has a different return type than the class itself"

    assert internal_init_argspec.defaults is None, (
        f"{cls.__name__}.internal_init has one or more default values, internal_init methods cannot"
        " have default values"
    )

    assert internal_init_argspec.args == [], (
        f"{cls.__name__}.internal_init has one or more positional arguments, internal_init methods"
        " can only have keyword-only arguments"
    )

    assert internal_init_argspec.kwonlyargs == (
        init_args_spec.args[1:] + init_args_spec.kwonlyargs  # exclude self
    ), f"{cls.__name__}.internal_init has different arguments than __init__"
