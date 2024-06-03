import ast
import inspect
from typing import Type, cast

import dagster as dagster
import pytest
from dagster._utils import ISubclassesMustSpecifyAllArgs
from dagster._utils.test import get_all_direct_subclasses_of_marker

SPECIFY_ALL_ARGS_SUBCLASSES = get_all_direct_subclasses_of_marker(ISubclassesMustSpecifyAllArgs)


@pytest.mark.parametrize("cls", SPECIFY_ALL_ARGS_SUBCLASSES)
def test_dagster_internal_init_class_follow_rules(cls: Type):
    implementers = get_all_direct_subclasses_of_marker(cls)
    init_params = inspect.signature(cls.__init__).parameters
    init_params_no_self = {k for k, v in init_params.items() if k != "self"}

    for implementer in implementers:
        implementer_init_fn = next(
            fd
            for fd in cast(ast.ClassDef, ast.parse(inspect.getsource(implementer)).body[0]).body
            if isinstance(fd, ast.FunctionDef) and fd.name == "__init__"
        )

        last_init_expression = implementer_init_fn.body[-1]
        assert isinstance(last_init_expression, ast.Expr)
        assert isinstance(last_init_expression.value, ast.Call)

        # ensure func name is right

        kwargs = last_init_expression.value.keywords
        kwarg_names = [kw.arg for kw in kwargs]

        assert (
            set(kwarg_names) == init_params_no_self
        ), f"{implementer.__name__} must specify all args to super().__init__"
