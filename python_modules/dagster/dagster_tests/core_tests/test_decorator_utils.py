from dagster.core.decorator_utils import (
    format_docstring_for_description,
    get_function_params,
    validate_expected_params,
)


def decorated_function_one_positional():
    def foo(bar):
        return bar

    return foo


def decorated_function_two_positionals_one_kwarg():
    def foo_kwarg(bar, baz, qux=True):
        return bar, baz, qux

    return foo_kwarg


def test_one_required_positional_param():
    positionals = ["bar"]
    fn_params = get_function_params(decorated_function_one_positional())
    assert {fn_param.name for fn_param in fn_params} == {"bar"}
    assert not validate_expected_params(fn_params, positionals)


def test_required_positional_parameters_not_missing():
    positionals = ["bar", "baz"]

    fn_params = get_function_params(decorated_function_two_positionals_one_kwarg())
    assert {fn_param.name for fn_param in fn_params} == {"bar", "qux", "baz"}

    assert not validate_expected_params(fn_params, positionals)

    fn_params = get_function_params(decorated_function_one_positional())
    assert validate_expected_params(fn_params, positionals) == "baz"


def test_format_docstring_for_description():
    def multiline_indented_docstring():
        """
        abc
        123
        """

    multiline_indented_docstring_expected = "abc\n123"

    assert (
        format_docstring_for_description(multiline_indented_docstring)
        == multiline_indented_docstring_expected
    )

    def no_indentation_at_start():
        """abc
        123
        """

    no_indentation_at_start_expected = "abc\n123"

    assert (
        format_docstring_for_description(no_indentation_at_start)
        == no_indentation_at_start_expected
    )
