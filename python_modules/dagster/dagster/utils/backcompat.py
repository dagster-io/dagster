import warnings
from typing import Callable, Optional, TypeVar, cast

import dagster._check as check

T = TypeVar("T")

EXPERIMENTAL_WARNING_HELP = (
    "To mute warnings for experimental functionality, invoke"
    ' warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning) or use'
    " one of the other methods described at"
    " https://docs.python.org/3/library/warnings.html#describing-warning-filters."
)


def canonicalize_backcompat_args(
    new_val: T, new_arg: str, old_val: T, old_arg: str, breaking_version: str, **kwargs: object
) -> T:
    """
    Utility for managing backwards compatibility of two related arguments.

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
    coerce_old_to_new = cast(Optional[Callable], kwargs.get("coerce_old_to_new"))
    additional_warn_txt = kwargs.get("additional_warn_txt")
    # stacklevel=3 punches up to the caller of canonicalize_backcompat_args
    stacklevel = kwargs.get("stacklevel", 3)

    check.str_param(new_arg, "new_arg")
    check.str_param(old_arg, "old_arg")
    check.opt_callable_param(coerce_old_to_new, "coerce_old_to_new")
    check.opt_str_param(additional_warn_txt, "additional_warn_txt")
    check.opt_int_param(stacklevel, "stacklevel")
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
            (" " + additional_warn_txt) if additional_warn_txt else ""
        )
        deprecation_warning(
            f'Argument "{old_arg}"', breaking_version, _additional_warn_txt, stacklevel + 1
        )
        return coerce_old_to_new(old_val) if coerce_old_to_new else old_val

    return new_val


def deprecation_warning(
    subject: str,
    breaking_version: str,
    additional_warn_txt: Optional[str] = None,
    stacklevel: int = 3,
):
    warnings.warn(
        f"{subject} is deprecated and will be removed in {breaking_version}."
        + ((" " + additional_warn_txt) if additional_warn_txt else ""),
        category=DeprecationWarning,
        stacklevel=stacklevel,
    )


def rename_warning(
    new_name: str,
    old_name: str,
    breaking_version: str,
    additional_warn_txt: Optional[str] = None,
    stacklevel: int = 3,
) -> None:
    """
    Common utility for managing backwards compatibility of renaming.
    """
    warnings.warn(
        '"{old_name}" is deprecated and will be removed in {breaking_version}, use "{new_name}" instead.'.format(
            old_name=old_name,
            new_name=new_name,
            breaking_version=breaking_version,
        )
        + ((" " + additional_warn_txt) if additional_warn_txt else ""),
        category=DeprecationWarning,
        stacklevel=stacklevel,
    )


class ExperimentalWarning(Warning):
    pass


def experimental_warning(message: str, stacklevel: int = 3) -> None:
    warnings.warn(
        f"{message}. {EXPERIMENTAL_WARNING_HELP}",
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_fn_warning(name: str, stacklevel: int = 3) -> None:
    """Utility for warning that a function is experimental"""
    warnings.warn(
        '"{name}" is an experimental function. It may break in future versions, even between dot'
        " releases. {help}".format(name=name, help=EXPERIMENTAL_WARNING_HELP),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_decorator_warning(name: str, stacklevel: int = 3) -> None:
    """Utility for warning that a decorator is experimental"""
    warnings.warn(
        f'"{name}" is an experimental decorator. It may break in future versions, even between dot'
        f" releases. {EXPERIMENTAL_WARNING_HELP}",
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_class_warning(name: str, stacklevel: int = 3) -> None:
    """Utility for warning that a class is experimental. Expected to be called from the class's
    __init__ method.

    Usage:

    .. code-block:: python

        class MyExperimentalClass:
            def __init__(self, some_arg):
                experimental_class_warning('MyExperimentalClass')
                # do other initialization stuff
    """
    warnings.warn(
        '"{name}" is an experimental class. It may break in future versions, even between dot'
        " releases. {help}".format(name=name, help=EXPERIMENTAL_WARNING_HELP),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_arg_warning(arg_name: str, fn_name: str, stacklevel: int = 3) -> None:
    """Utility for warning that an argument to a function is experimental"""
    warnings.warn(
        '"{arg_name}" is an experimental argument to function "{fn_name}". '
        "It may break in future versions, even between dot releases. {help}".format(
            arg_name=arg_name, fn_name=fn_name, help=EXPERIMENTAL_WARNING_HELP
        ),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_functionality_warning(desc: str, stacklevel: int = 3) -> None:
    """Utility for warning that a particular functionality is experimental"""
    warnings.warn(
        f"{desc} is currently experimental functionality. It may break in future versions, even "
        f"between dot releases. {EXPERIMENTAL_WARNING_HELP}",
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_class_param_warning(param_name: str, class_name: str, stacklevel=3) -> None:
    """Utility for warning that an argument to a constructor is experimental"""
    warnings.warn(
        (
            f'"{param_name}" is an experimental parameter to the class "{class_name}". It may '
            f"break in future versions, even between dot releases. {EXPERIMENTAL_WARNING_HELP}"
        ),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )
