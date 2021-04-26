from dagster import check
from dagster.seven import funcsigs


def split_function_parameters(fn, expected_positionals):
    check.callable_param(fn, "fn")
    check.list_param(expected_positionals, "expected_positionals", str)
    fn_params = list(funcsigs.signature(fn).parameters.values())
    return fn_params[0 : len(expected_positionals)], fn_params[len(expected_positionals) :]


def validate_decorated_fn_positionals(decorated_fn_positionals, expected_positionals):
    if len(decorated_fn_positionals) < len(expected_positionals):
        return expected_positionals[0]
    for expected_name, actual in zip(expected_positionals, decorated_fn_positionals):
        if expected_name != "*":
            possible_names = {
                "_",
                expected_name,
                "_{expected}".format(expected=expected_name),
                "{expected}_".format(expected=expected_name),
            }
            if (
                actual.kind
                not in [
                    funcsigs.Parameter.POSITIONAL_OR_KEYWORD,
                    funcsigs.Parameter.POSITIONAL_ONLY,
                ]
            ) or (actual.name not in possible_names):
                return expected_name


def is_required_param(param):
    return param.default == funcsigs.Parameter.empty


def positional_arg_name_list(params):
    return list(
        map(
            lambda p: p.name,
            filter(
                lambda p: p.kind
                in [funcsigs.Parameter.POSITIONAL_OR_KEYWORD, funcsigs.Parameter.POSITIONAL_ONLY],
                params,
            ),
        )
    )
