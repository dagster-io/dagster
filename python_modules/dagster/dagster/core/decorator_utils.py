from dagster import check
from dagster.seven import funcsigs


class InvalidDecoratedFunctionInfo:
    TYPES = {"vararg": 1, "missing_name": 2, "extra": 3}

    def __init__(self, error_type, param=None, missing_names=None):
        self.error_type = error_type
        self.param = param
        self.missing_names = missing_names


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


def validate_decorated_fn_input_args(input_def_names, decorated_fn_input_args):
    used_inputs = set()
    has_kwargs = False

    for param in decorated_fn_input_args:
        if param.kind == funcsigs.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == funcsigs.Parameter.VAR_POSITIONAL:
            return InvalidDecoratedFunctionInfo(
                error_type=InvalidDecoratedFunctionInfo.TYPES["vararg"]
            )

        else:
            if param.name not in input_def_names:
                return InvalidDecoratedFunctionInfo(
                    InvalidDecoratedFunctionInfo.TYPES["missing_name"], param=param.name
                )
            else:
                used_inputs.add(param.name)

    undeclared_inputs = input_def_names - used_inputs
    if not has_kwargs and undeclared_inputs:
        return InvalidDecoratedFunctionInfo(
            InvalidDecoratedFunctionInfo.TYPES["extra"], missing_names=undeclared_inputs
        )


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
