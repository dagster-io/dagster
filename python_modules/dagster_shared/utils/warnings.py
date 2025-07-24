import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable, Optional, TypeVar

from dagster_shared import check

T = TypeVar("T")

_warnings_on = ContextVar("_warnings_on", default=True)

# ########################
# ##### PREVIEW
# ########################


class PreviewWarning(Warning):
    pass


def preview_warning(
    subject: str,
    additional_warn_text: Optional[str] = None,
    stacklevel: int = 3,
):
    if not _warnings_on.get():
        return

    warnings.warn(
        f"{subject} is currently in preview, and may have breaking changes in patch version releases. "
        f"This feature is not considered ready for production use."
        + ((" " + additional_warn_text) if additional_warn_text else ""),
        category=PreviewWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### BETA
# ########################


class BetaWarning(Warning):
    pass


def beta_warning(
    subject: str,
    additional_warn_text: Optional[str] = None,
    stacklevel: int = 3,
):
    if not _warnings_on.get():
        return

    warnings.warn(
        f"{subject} is currently in beta, and may have breaking changes in minor version releases, "
        f"with behavior changes in patch releases."
        + ((" " + additional_warn_text) if additional_warn_text else ""),
        category=BetaWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### SUPERSEDED
# ########################


class SupersessionWarning(FutureWarning):
    pass


def supersession_warning(
    subject: str,
    additional_warn_text: Optional[str] = None,
    stacklevel: int = 3,
):
    if not _warnings_on.get():
        return

    warnings.warn(
        f"{subject} is superseded and its usage is discouraged."
        + ((" " + additional_warn_text) if additional_warn_text else ""),
        category=SupersessionWarning,
        stacklevel=stacklevel,
    )


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
    if not _warnings_on.get():
        return

    warnings.warn(
        f"{subject} is deprecated and will be removed in {breaking_version}."
        + ((" " + additional_warn_text) if additional_warn_text else ""),
        category=DeprecationWarning,
        stacklevel=stacklevel,
    )


# ########################
# ##### Config arg warning
# ########################

CONFIG_WARNING_HELP = (
    "To mute this warning, invoke"
    ' warnings.filterwarnings("ignore", category=dagster.ConfigArgumentWarning) or use'
    " one of the other methods described at"
    " https://docs.python.org/3/library/warnings.html#describing-warning-filters."
)


class ConfigArgumentWarning(SyntaxWarning):
    pass


def config_argument_warning(param_name: str, function_name: str) -> None:
    warnings.warn(
        f"Parameter '{param_name}' on op/asset function '{function_name}' was annotated as"
        " a dagster.Config type. Did you mean to name this parameter 'config'"
        " instead?\n\n"
        f"{CONFIG_WARNING_HELP}",
        ConfigArgumentWarning,
    )


# ########################
# ##### DISABLE DAGSTER WARNINGS
# ########################


@contextmanager
def disable_dagster_warnings() -> Iterator[None]:
    # If warnings are already disabled, do nothing. Nested resets of the token in finally blocks
    # have occasionally had inconsistent ordering in the past, which can lead to `_warnings_on`
    # being permanently turned off. By instantly returning, we prevent this nesting.
    if not _warnings_on.get():
        yield
    else:
        token = None
        try:
            token = _warnings_on.set(False)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=DeprecationWarning)
                warnings.simplefilter("ignore", category=SupersessionWarning)
                warnings.simplefilter("ignore", category=PreviewWarning)
                warnings.simplefilter("ignore", category=BetaWarning)
                yield
        finally:
            if token is not None:
                _warnings_on.reset(token)
