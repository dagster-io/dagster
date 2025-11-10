from collections.abc import Callable

import dagster as dg
from dagster.components.component.template_vars import is_template_var
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.context import ComponentLoadContext


def test_template_udf_decorator():
    @dg.template_var
    def my_udf(context: ComponentLoadContext) -> Callable[[str], str]:
        return lambda x: f"udf_{x}"

    assert is_template_var(my_udf)
    assert my_udf(ComponentTree.for_test().decl_load_context)("test") == "udf_test"


def test_template_udf_decorator_with_parens():
    @dg.template_var()
    def my_udf(context: ComponentLoadContext) -> Callable[[str], str]:
        return lambda x: f"udf_{x}"

    assert is_template_var(my_udf)
    assert my_udf(ComponentTree.for_test().decl_load_context)("test") == "udf_test"


def test_template_udf_decorator_preserves_function_metadata():
    @dg.template_var
    def my_udf(context: ComponentLoadContext) -> Callable[[str], str]:
        """Test docstring."""
        return lambda x: f"udf_{x}"

    assert my_udf.__name__ == "my_udf"
    assert my_udf.__doc__ == "Test docstring."


def test_is_template_udf():
    def regular_fn() -> Callable[[str], str]:
        return lambda x: f"regular_{x}"

    @dg.template_var
    def udf_fn(context: ComponentLoadContext) -> Callable[[str], str]:
        return lambda x: f"udf_{x}"

    assert not is_template_var(regular_fn)
    assert is_template_var(udf_fn)


def test_template_var_decorator():
    @dg.template_var
    def my_var(context: ComponentLoadContext) -> str:
        return "var_value"

    assert is_template_var(my_var)
    assert my_var(ComponentTree.for_test().decl_load_context) == "var_value"


def test_template_var_decorator_with_parens():
    @dg.template_var()
    def my_var(context: ComponentLoadContext) -> str:
        return "var_value"

    assert is_template_var(my_var)
    assert my_var(ComponentTree.for_test().decl_load_context) == "var_value"


def test_template_var_decorator_preserves_function_metadata():
    @dg.template_var
    def my_var(context: ComponentLoadContext) -> str:
        """Test docstring."""
        return "var_value"

    assert my_var.__name__ == "my_var"
    assert my_var.__doc__ == "Test docstring."


def test_is_template_var():
    def regular_fn() -> str:
        return "regular_value"

    @dg.template_var
    def var_fn(context: ComponentLoadContext) -> str:
        return "var_value"

    assert not is_template_var(regular_fn)
    assert is_template_var(var_fn)
