import functools
import re
import textwrap
from inspect import Parameter, signature
from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
)

from typing_extensions import (
    Concatenate,
    ParamSpec,
    TypeGuard,
    get_type_hints as typing_get_type_hints,
)

from dagster._core.errors import DagsterInvalidDefinitionError

R = TypeVar("R")
T = TypeVar("T")
P = ParamSpec("P")


def get_valid_name_permutations(param_name: str) -> Set[str]:
    """Get all underscore permutations for provided arg name."""
    return {
        "_",
        param_name,
        f"_{param_name}",
        f"{param_name}_",
    }


def _is_param_valid(param: Parameter, expected_positional: str) -> bool:
    # The "*" character indicates that we permit any name for this positional parameter.
    if expected_positional == "*":
        return True

    possible_kinds = {Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_ONLY}

    return (
        param.name in get_valid_name_permutations(expected_positional)
        and param.kind in possible_kinds
    )


def get_function_params(fn: Callable[..., Any]) -> Sequence[Parameter]:
    return list(signature(fn).parameters.values())


def get_type_hints(fn: Callable) -> Mapping[str, Any]:
    target = fn.func if isinstance(fn, functools.partial) else fn

    try:
        return typing_get_type_hints(target, include_extras=True)
    except NameError as e:
        match = re.search(r"'(\w+)'", str(e))
        assert match
        annotation = match[1]
        raise DagsterInvalidDefinitionError(
            f'Failed to resolve type annotation "{annotation}" in function {target.__name__}. This'
            " can occur when the parameter has a string annotation that references either: (1) a"
            " type defined in a local scope (2) a type that is defined or imported in an `if"
            " TYPE_CHECKING` block. Note that if you are including `from __future__ import"
            " annotations`, all annotations in that module are stored as strings. Suggested"
            " solutions include: (1) convert the annotation to a non-string annotation; (2) move"
            " the type referenced by the annotation out of local scope or a `TYPE_CHECKING` block."
        )


def validate_expected_params(
    params: Sequence[Parameter], expected_params: Sequence[str]
) -> Optional[str]:
    """Returns first missing positional, if any, otherwise None."""
    expected_idx = 0
    for expected_param in expected_params:
        if expected_idx >= len(params) or not _is_param_valid(params[expected_idx], expected_param):
            return expected_param
        expected_idx += 1
    return None


def is_required_param(param: Parameter) -> bool:
    return param.default == Parameter.empty


def positional_arg_name_list(params: Sequence[Parameter]) -> Sequence[str]:
    accepted_param_types = {
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.POSITIONAL_ONLY,
    }
    return [p.name for p in params if p.kind in accepted_param_types]


def param_is_var_keyword(param: Parameter) -> bool:
    return param.kind == Parameter.VAR_KEYWORD


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
                    + textwrap.dedent(docstring[first_newline_pos + 1 :])
                ).strip()
    else:
        return None


# Type-ignores are used throughout the codebase when this function returns False to ignore the type
# error arising from assuming
# When/if `StrictTypeGuard` is supported, we can drop `is_context_not_provided` since a False from
# `has_at_least_one_parameter` will be sufficient.
def has_at_least_one_parameter(
    fn: Union[Callable[Concatenate[T, P], R], Callable[P, R]],
) -> TypeGuard[Callable[Concatenate[T, P], R]]:
    return len(get_function_params(fn)) >= 1
