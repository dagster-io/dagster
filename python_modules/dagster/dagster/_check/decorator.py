from functools import update_wrapper

import dagster._check as check
from dagster._check.builder import EvalContext, build_check_call_str


class JitCheckedFn:
    def __init__(self, fn, annotations):
        self._fn = fn
        self._annotations = annotations
        self._eval_ctx = EvalContext.capture_from_frame(
            2,
            add_to_local_ns={},
        )

    def __call__(self, *args, **kwargs):
        checks = [
            build_check_call_str(
                ttype=ttype,
                name=name,
                eval_ctx=self._eval_ctx,
            )
            for name, ttype in self._annotations.items()
        ]
        checks_block_str = ",\n         ".join(checks)
        args_str = ", ".join(name for name in self._annotations.keys())

        fn_str = f"""
def {self._fn.__name__}(self, {args_str}):
    return self._fn(
        {checks_block_str}
    )
        """

        if "check" not in self._eval_ctx.global_ns:
            self._eval_ctx.global_ns["check"] = check

        call = self._eval_ctx.compile_fn(
            fn_str,
            fn_name=self._fn.__name__,
        )
        self.__class__.__call__ = call
        return call(self, *args, **kwargs)


def checked(fn):
    """Decorator for adding runtime type checking based on type annotations."""
    annotations = getattr(fn, "__annotations__", None)

    # make a dynamic subclass to be able to hot swap __call__ post compilation
    new_cls = type(
        f"__checked_{fn.__name__}",
        (JitCheckedFn,),
        {},
    )
    checked_fn = new_cls(
        fn=fn,
        annotations=annotations,
    )
    return update_wrapper(
        wrapper=checked_fn,
        wrapped=fn,
    )
