import inspect
from abc import ABC
from functools import update_wrapper
from types import MethodType

import dagster_shared.check as check
from dagster_shared.check.builder import (
    INJECTED_DEFAULT_VALS_LOCAL_VAR,
    EvalContext,
    build_args_and_assignment_strs,
    build_check_call_str,
)


class CheckedFnWrapper(ABC):
    """Output of the @checked decorator, this class holds a reference to the decorated function
    and upon first invocation compiles a wrapping function that performs run time type checks on
    annotated inputs.

    This class is not directly instantiated, but instead dynamic subclasses are created for each
    callsite allowing the __call__ method to be replaced[1] with the compiled function to achieve
    a single stack frame of over head for this decorator in best cases scenarios.


    [1] __call__ can not be replaced on instances, only classes.
    """

    def __init__(self, fn):
        self._target_fn = fn
        self._eval_ctx = EvalContext.capture_from_frame(2)

    def __get__(self, instance, _=None):
        """Allow the decorated function to be bound to instances to support class methods."""
        if instance:
            return MethodType(self, instance)
        return self

    def __call__(self, *args, **kwargs):
        signature = inspect.signature(self._target_fn)
        lines = []
        param_names = []
        defaults = {}
        for name, param in signature.parameters.items():
            if param.annotation != param.empty:
                param_str = build_check_call_str(
                    ttype=param.annotation,
                    name=name,
                    eval_ctx=self._eval_ctx,
                )
            else:
                param_str = param.name

            if param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD):
                param_str = f"{param.name}={param_str}"

            param_names.append(param.name)
            if param.default != param.empty:
                defaults[param.name] = param.default

            lines.append(param_str)

        lazy_imports_str = "\n    ".join(
            f"from {module} import {t}" for t, module in self._eval_ctx.lazy_imports.items()
        )
        args_str, set_calls_str = build_args_and_assignment_strs(
            param_names,
            defaults,
            kw_only=False,
        )
        param_block = ",\n        ".join(lines)

        checked_fn_name = f"__checked_{self._target_fn.__name__}"

        fn_str = f"""
def {checked_fn_name}(__checked_wrapper{args_str}):
    {lazy_imports_str}
    {set_calls_str}
    return __checked_wrapper._target_fn(
        {param_block}
    )
        """

        if "check" not in self._eval_ctx.global_ns:
            self._eval_ctx.global_ns["check"] = check

        self._eval_ctx.local_ns[INJECTED_DEFAULT_VALS_LOCAL_VAR] = defaults

        call = self._eval_ctx.compile_fn(
            fn_str,
            fn_name=checked_fn_name,
        )

        self.__class__.__call__ = call
        return call(self, *args, **kwargs)


def checked(fn):
    """Decorator for adding runtime type checking based on type annotations."""
    # if nothing can be checked, return the original fn
    annotations = getattr(fn, "__annotations__", None)
    if not annotations or (len(annotations) == 1 and set(annotations.keys()) == {"return"}):
        return fn

    # make a dynamic subclass to be able to hot swap __call__ post compilation
    class _DynamicCheckedFnWrapper(CheckedFnWrapper): ...

    checked_fn = _DynamicCheckedFnWrapper(fn)
    return update_wrapper(
        wrapper=checked_fn,
        wrapped=fn,
    )
