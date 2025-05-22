from typing import Callable

from dagster.components.component.template_vars import template_var


@template_var
def foo(context) -> str:
    return "value_for_foo"


@template_var
def a_udf(context) -> Callable:
    return lambda: "a_udf_value"


@template_var
def a_udf_with_args(context) -> Callable:
    return lambda x: f"a_udf_value_{x}"
