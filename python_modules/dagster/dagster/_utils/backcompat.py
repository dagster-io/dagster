import warnings
from contextlib import contextmanager
from typing import Callable, Iterator, Optional, TypeVar

import dagster._check as check
from dagster._core.decorator_utils import (
    Decoratable,
    apply_context_manager_decorator,
)

T = TypeVar("T")

# ########################
# ##### DEPRECATED
# ########################


def canonicalize_backcompat_args(
    new_val: T,
    new_arg: str,
    old_val: T,
    old_arg: str,
    breaking_version: str,
    coerce_old_to_new: Optional[Callable[[T], T]] = None,
    additional_warn_text: Optional[str] = None,
    # stacklevel=3 punches up to the caller of canonicalize_backcompat_args
    stacklevel: int = 3,
) -> T:
    """Utility for managing backwards compatibility of two related arguments.

    For example if you had an existing function

    def is_new(old_flag):
        return not new_flag

    And you decided you wanted a new function to be:

    def is_new(new_flag):
        return new_flag

    However you want an in between period where either flag is accepted. Use
    canonicalize_backcompat_args to manage that:

    def is_new(old_flag=None, new_flag=None):
        return canonicalize_backcompat_args(
            new_val=new_flag,
            new_arg='new_flag',
            old_val=old_flag,
            old_arg='old_flag',
            breaking_version='0.9.0',
            coerce_old_to_new=lambda val: not val,
        )


    In this example, if the caller sets both new_flag and old_flag, it will fail by throwing
    a CheckError. If the caller sets old_flag, it will run it through the coercion function
    , warn, and then execute.

    canonicalize_backcompat_args returns the value as if *only* new_val were specified
    """
    check.str_param(new_arg, "new_arg")
    check.str_param(old_arg, "old_arg")
    check.opt_callable_param(coerce_old_to_new, "coerce_old_to_new")
    check.opt_str_param(additional_warn_text, "additional_warn_text")
    check.int_param(stacklevel, "stacklevel")
    if new_val is not None:
        if old_val is not None:
            check.failed(
                'Do not use deprecated "{old_arg}" now that you are using "{new_arg}".'.format(
                    old_arg=old_arg, new_arg=new_arg
                )
            )
        return new_val
    if old_val is not None:
        _additional_warn_txt = f'Use "{new_arg}" instead.' + (
            (" " + additional_warn_text) if additional_warn_text else ""
        )
        deprecation_warning(
            f'Argument "{old_arg}"', breaking_version, _additional_warn_txt, stacklevel + 1
        )
        return coerce_old_to_new(old_val) if coerce_old_to_new else old_val

    return new_val


def deprecation_warning(
    subject: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = None,
    stacklevel: int = 3,
):
    warnings.warn(
        f"{subject} is deprecated and will be removed in {breaking_version}."
        + ((" " + additional_warn_text) if additional_warn_text else ""),
        category=DeprecationWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### EXPERIMENTAL
# ########################

EXPERIMENTAL_WARNING_HELP = (
    "To mute warnings for experimental functionality, invoke"
    ' warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning) or use'
    " one of the other methods described at"
    " https://docs.python.org/3/library/warnings.html#describing-warning-filters."
)


class ExperimentalWarning(Warning):
    pass


def experimental_warning(
    subject: str, additional_warn_text: Optional[str] = None, stacklevel: int = 3
) -> None:
    extra_text = ((f" {additional_warn_text} " if additional_warn_text else ""),)
    warnings.warn(
        (
            f"{subject} is experimental. It may break in future versions, even between dot"
            f" releases.{extra_text}{EXPERIMENTAL_WARNING_HELP}"
        ),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_arg_warning(arg_name: str, fn_name: str, stacklevel: int = 3) -> None:
    """Utility for warning that an argument to a function is experimental."""
    warnings.warn(
        '"{arg_name}" is an experimental argument to function "{fn_name}". '
        "It may break in future versions, even between dot releases. {help}".format(
            arg_name=arg_name, fn_name=fn_name, help=EXPERIMENTAL_WARNING_HELP
        ),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### QUIET EXPERIMENTAL WARNINGS
# ########################


T_Decoratable = TypeVar("T_Decoratable", bound=Decoratable)


def quiet_experimental_warnings(__obj: T_Decoratable) -> T_Decoratable:
    """Mark a method/function as ignoring experimental warnings. This quiets any "experimental" warnings
    emitted inside the passed callable. Useful when we want to use experimental features internally
    in a way that we don't want to warn users about.

    Usage:

        .. code-block:: python

            @quiet_experimental_warnings
            def invokes_some_experimental_stuff(my_arg):
                my_experimental_function(my_arg)
    """

    @contextmanager
    def suppress_experimental_warnings() -> Iterator[None]:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            yield

    return apply_context_manager_decorator(__obj, suppress_experimental_warnings)
