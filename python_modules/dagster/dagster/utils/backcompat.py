import warnings
from functools import wraps

from dagster import check

EXPERIMENTAL_WARNING_HELP = (
    "To mute warnings for experimental functionality, invoke"
    ' warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning) or use'
    " one of the other methods described at"
    " https://docs.python.org/3/library/warnings.html#describing-warning-filters."
)


def canonicalize_backcompat_args(new_val, new_arg, old_val, old_arg, breaking_version, **kwargs):
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
    coerce_old_to_new = kwargs.get("coerce_old_to_new")
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
        warnings.warn(
            '"{old_arg}" is deprecated and will be removed in {breaking_version}, use "{new_arg}" instead.'.format(
                old_arg=old_arg, new_arg=new_arg, breaking_version=breaking_version
            )
            + ((" " + additional_warn_txt) if additional_warn_txt else ""),
            stacklevel=stacklevel,
        )
        return coerce_old_to_new(old_val) if coerce_old_to_new else old_val

    return new_val


def rename_warning(new_name, old_name, breaking_version, additional_warn_txt=None, stacklevel=3):
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
        stacklevel=stacklevel,
    )


class ExperimentalWarning(Warning):
    pass


def experimental_fn_warning(name, stacklevel=3):
    """Utility for warning that a function is experimental"""
    warnings.warn(
        '"{name}" is an experimental function. It may break in future versions, even between dot'
        " releases. {help}".format(name=name, help=EXPERIMENTAL_WARNING_HELP),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental_class_warning(name, stacklevel=3):
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


def experimental_arg_warning(arg_name, fn_name, stacklevel=3):
    """Utility for warning that an argument to a function is experimental"""
    warnings.warn(
        '"{arg_name}" is an experimental argument to function "{fn_name}". '
        "It may break in future versions, even between dot releases. {help}".format(
            arg_name=arg_name, fn_name=fn_name, help=EXPERIMENTAL_WARNING_HELP
        ),
        ExperimentalWarning,
        stacklevel=stacklevel,
    )


def experimental(fn):
    """
    Spews an "experimental" warning whenever the given callable is called. If the argument is a
    class, this means the warning will be emitted when the class is instantiated.

    Usage:

        .. code-block:: python

            @experimental
            def my_experimental_function(my_arg):
                do_stuff()
    """
    check.callable_param(fn, "fn")

    @wraps(fn)
    def _inner(*args, **kwargs):
        experimental_fn_warning(fn.__name__, stacklevel=3)
        return fn(*args, **kwargs)

    return _inner
