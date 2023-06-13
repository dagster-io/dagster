import inspect
from typing import Callable, cast

from typing_extensions import ParamSpec, TypeVar

R = TypeVar("R")
Pf = ParamSpec("Pf")
Pt = ParamSpec("Pt")


def mirror_signature_of(fn_from: Callable[Pf, R]) -> Callable[[Callable[Pt, R]], Callable[Pf, R]]:
    """Copies the signature from the provided function to the decorated function. This is useful when you want
    to wrap a function but want to preserve its signature (e.g. if the signature is used for introspection).

    Example:
        def foo(a: int, b: int) -> int:
            return a + b

        def print_args(fn):
            @mirror_signature_of(fn)
            def _wrapper(*args, **kwargs):
                print(args, kwargs)
                return fn(*args, **kwargs)
            return _wrapper

        print(inspect.signature(foo))  # (a: int, b: int) -> int
        print(inspect.signature(print_args(foo)))  # (a: int, b: int) -> int
    """

    def copy_signature(fn_to: Callable[Pt, R]) -> Callable[Pf, R]:
        fn_to.__signature__ = inspect.signature(fn_from)
        return cast(Callable[Pf, R], fn_to)

    return copy_signature
