from typing import Callable

import dagster as dg


@dg.template_var
def foo(context) -> str:
    return "value_for_foo"


@dg.template_var
def a_udf(context) -> Callable:
    return lambda: "a_udf_value"


@dg.template_var
def a_udf_with_args(context) -> Callable:
    return lambda x: f"a_udf_value_{x}"
