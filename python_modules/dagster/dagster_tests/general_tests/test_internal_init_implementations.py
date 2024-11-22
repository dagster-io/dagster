from inspect import Parameter, signature
from typing import Tuple, Type

import dagster as dagster
import pytest
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._utils import IHasInternalInit
from dagster._utils.test import get_all_direct_subclasses_of_marker

INTERNAL_INIT_SUBCLASSES = get_all_direct_subclasses_of_marker(IHasInternalInit)


def _is_namedtuple(cls: type) -> bool:
    return safe_is_subclass(cls, tuple) and hasattr(cls, "_fields")


@pytest.mark.parametrize("cls", INTERNAL_INIT_SUBCLASSES)
def test_dagster_internal_init_class_follow_rules(cls: type):
    assert hasattr(
        cls, "dagster_internal_init"
    ), f"{cls.__name__} does not have dagster_internal_init method"

    dagster_internal_init_params = signature(cls.dagster_internal_init).parameters

    init_params = signature(cls.__init__).parameters
    # check __new__ instead of __init__ for namedtuples
    if _is_namedtuple(cls):
        # drop cls parameter
        init_params = {k: v for k, v in signature(cls.__new__).parameters.items() if k != "cls"}

    dagster_internal_init_return = signature(cls.dagster_internal_init).return_annotation

    assert (
        dagster_internal_init_return == cls or dagster_internal_init_return == cls.__name__
    ), f"{cls.__name__}.dagster_internal_init has a different return type than the class itself"

    assert all(p.default == Parameter.empty for p in dagster_internal_init_params.values()), (
        f"{cls.__name__}.dagster_internal_init has one or more default values,"
        " dagster_internal_init methods cannot have default values"
    )

    assert all(
        p.kind == Parameter.KEYWORD_ONLY or (p.name == "kwargs" and p.kind == Parameter.VAR_KEYWORD)
        for p in dagster_internal_init_params.values()
    ), (
        f"{cls.__name__}.dagster_internal_init has one or more positional arguments,"
        " dagster_internal_init methods can only have keyword-only arguments"
    )

    excluded_args = getattr(cls, "_dagster_internal_init_excluded_args", set())
    dagster_internal_init_expected_param_names = [
        k for k in init_params.keys() if k not in excluded_args and k != "self"
    ]
    assert (
        [*dagster_internal_init_params.keys()] == dagster_internal_init_expected_param_names
    ), f"{cls.__name__}.dagster_internal_init has different arguments than __init__"
