import inspect
from typing import Any

from dagster._core.decorator_utils import (
    format_docstring_for_description,
    get_function_params,
    get_type_hints,
    validate_expected_params,
)


class Widget:
    pass


def widget_signature(widget: Widget) -> Widget:
    raise NotImplementedError


def string_annotated_widget_signature(widget: "Widget") -> "Widget":
    raise NotImplementedError


class CallableWithCustomSignature:
    def __init__(self, sig: inspect.Signature) -> None:
        self.__signature__ = sig

    def __call__(self, **kwargs: Any) -> Any: ...


class CallableWithoutCustomSignature:
    def __call__(self, widget: Widget) -> Widget:
        raise NotImplementedError


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
        """Abc
        123.
        """

    multiline_indented_docstring_expected = "Abc\n123."

    assert (
        format_docstring_for_description(multiline_indented_docstring)
        == multiline_indented_docstring_expected
    )

    def no_indentation_at_start():
        """Abc
        123.
        """

    no_indentation_at_start_expected = "Abc\n123."

    assert (
        format_docstring_for_description(no_indentation_at_start)
        == no_indentation_at_start_expected
    )

    def indentation_at_start():
        """
        abc
        123.
        """  # noqa

    indentation_at_start_expected = "abc\n123."

    assert format_docstring_for_description(indentation_at_start) == indentation_at_start_expected

    def summary_line_and_description():
        """This is the summary line.

        This is a longer description of what my asset does, and I'd like for the
        newline between this paragraph and the summary line to be preserved.
        """

    indentation_at_start_expected = (
        "This is the summary line.\n\nThis is a longer description of what my asset does, and I'd"
        " like for the\nnewline between this paragraph and the summary line to be preserved."
    )

    assert (
        format_docstring_for_description(summary_line_and_description)
        == indentation_at_start_expected
    )


def test_empty():
    def empty_docstring():
        """"""  # noqa: D419

    assert format_docstring_for_description(empty_docstring) == ""


def test_get_type_hints_honors_custom_signature():
    # A callable object whose `__call__` only takes `**kwargs` but which advertises a custom
    # `__signature__`: hints must be keyed off the same signature `get_function_params` reads, or
    # callers match parameter names against annotations that describe a different function.
    wrapper = CallableWithCustomSignature(inspect.signature(widget_signature))

    assert [p.name for p in get_function_params(wrapper)] == ["widget"]
    assert get_type_hints(wrapper) == {"widget": Widget, "return": Widget}

    # String annotations in the signature are resolved, not passed through as strings.
    string_wrapper = CallableWithCustomSignature(
        inspect.signature(string_annotated_widget_signature)
    )
    assert get_type_hints(string_wrapper) == {"widget": Widget, "return": Widget}

    # Callables with no custom signature are unaffected.
    assert get_type_hints(widget_signature) == {"widget": Widget, "return": Widget}
    assert get_type_hints(CallableWithoutCustomSignature()) == {"widget": Widget, "return": Widget}
