from typing import Any, Callable, List, Optional

from dagster.seven import funcsigs


def _is_param_valid(param: funcsigs.Parameter, expected_positional: str) -> bool:
    # The "*" character indicates that we permit any name for this positional parameter.
    if expected_positional == "*":
        return True

    possible_names = {
        "_",
        expected_positional,
        f"_{expected_positional}",
        f"{expected_positional}_",
    }
    possible_kinds = {funcsigs.Parameter.POSITIONAL_OR_KEYWORD, funcsigs.Parameter.POSITIONAL_ONLY}

    return param.name in possible_names and param.kind in possible_kinds


def get_function_params(fn: Callable[..., Any]) -> List[funcsigs.Parameter]:
    return list(funcsigs.signature(fn).parameters.values())


def validate_expected_params(
    params: List[funcsigs.Parameter], expected_params: List[str]
) -> Optional[str]:
    """Returns first missing positional, if any, otherwise None"""
    expected_idx = 0
    for expected_param in expected_params:
        if expected_idx >= len(params) or not _is_param_valid(params[expected_idx], expected_param):
            return expected_param
        expected_idx += 1
    return None


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
