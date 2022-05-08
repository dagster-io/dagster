import textwrap
from typing import Any, Callable, List, Optional, Set

from dagster.seven import funcsigs


def get_valid_name_permutations(param_name: str) -> Set[str]:
    """Get all underscore permutations for provided arg name"""
    return {
        "_",
        param_name,
        f"_{param_name}",
        f"{param_name}_",
    }


def _is_param_valid(param: funcsigs.Parameter, expected_positional: str) -> bool:
    # The "*" character indicates that we permit any name for this positional parameter.
    if expected_positional == "*":
        return True

    possible_kinds = {funcsigs.Parameter.POSITIONAL_OR_KEYWORD, funcsigs.Parameter.POSITIONAL_ONLY}

    return (
        param.name in get_valid_name_permutations(expected_positional)
        and param.kind in possible_kinds
    )


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


def is_required_param(param: funcsigs.Parameter) -> bool:
    return param.default == funcsigs.Parameter.empty


def positional_arg_name_list(params: List[funcsigs.Parameter]) -> List[str]:
    accepted_param_types = {
        funcsigs.Parameter.POSITIONAL_OR_KEYWORD,
        funcsigs.Parameter.POSITIONAL_ONLY,
    }
    return [p.name for p in params if p.kind in accepted_param_types]


def param_is_var_keyword(param: funcsigs.Parameter) -> bool:
    return param.kind == funcsigs.Parameter.VAR_KEYWORD


def format_docstring_for_description(fn: Callable) -> Optional[str]:
    if fn.__doc__ is not None:
        docstring = fn.__doc__
        if len(docstring) > 0 and docstring[0].isspace():
            return textwrap.dedent(docstring).strip()
        else:
            first_newline_pos = docstring.find("\n")
            if first_newline_pos == -1:
                return docstring
            else:
                return (
                    docstring[: first_newline_pos + 1]
                    + textwrap.dedent(docstring[first_newline_pos + 1 :]).strip()
                )
    else:
        return None
