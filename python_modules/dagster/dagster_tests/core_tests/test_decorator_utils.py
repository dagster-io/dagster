from dagster.core.decorator_utils import get_function_params, validate_expected_params


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
