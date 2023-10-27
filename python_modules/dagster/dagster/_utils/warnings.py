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


def normalize_renamed_param(
    new_val: T,
    new_arg: str,
    old_val: T,
    old_arg: str,
    coerce_old_to_new: Optional[Callable[[T], T]] = None,
) -> T:
    """Utility for managing backwards compatibility of a renamed parameter.

    .. code-block::

       # The name of param `old_flag` is being updated to `new_flag`, but we are temporarily
       # accepting either param.
       def is_new(old_flag=None, new_flag=None):
           return canonicalize_backcompat_args(
               new_val=new_flag,
               new_arg='new_flag',
               old_val=old_flag,
               old_arg='old_flag',
               breaking_version='0.9.0',
               coerce_old_to_new=lambda val: not val,
           )

    In the above example, if the caller sets both new_flag and old_flag, it will fail by throwing
    a CheckError. If the caller sets the new_flag, it's returned unaltered. If the caller sets
    old_flag, it will return the old_flag run through the coercion function.
    """
    check.str_param(new_arg, "new_arg")
    check.str_param(old_arg, "old_arg")
    check.opt_callable_param(coerce_old_to_new, "coerce_old_to_new")
    if new_val is not None and old_val is not None:
        check.failed(f'Do not use deprecated "{old_arg}" now that you are using "{new_arg}".')
    elif old_val is not None:
        return coerce_old_to_new(old_val) if coerce_old_to_new else old_val
    else:
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
    extra_text = f" {additional_warn_text}" if additional_warn_text else ""
    warnings.warn(
        f"{subject} is experimental. It may break in future versions, even between dot"
        f" releases.{extra_text} {EXPERIMENTAL_WARNING_HELP}",
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### DISABLE DAGSTER WARNINGS
# ########################


@contextmanager
def disable_dagster_warnings() -> Iterator[None]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        warnings.simplefilter("ignore", category=ExperimentalWarning)
        yield


T_Decoratable = TypeVar("T_Decoratable", bound=Decoratable)


def suppress_dagster_warnings(__obj: T_Decoratable) -> T_Decoratable:
    """Mark a method/function as ignoring Dagster-generated warnings. This suppresses any
    `ExperimentalWarnings` or `DeprecationWarnings` when the function is called.

    Usage:

        .. code-block:: python

            @suppress_dagster_warnings
            def invokes_some_experimental_stuff(my_arg):
                my_experimental_function(my_arg)
    """
    return apply_context_manager_decorator(__obj, disable_dagster_warnings)
