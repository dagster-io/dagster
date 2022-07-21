from typing import Callable, TypeVar

T_Callable = TypeVar("T_Callable", bound=Callable)


def public(fn: T_Callable) -> T_Callable:
    setattr(fn, "_public", True)
    return fn


def is_public(fn: Callable) -> bool:
    return hasattr(fn, "_public") and getattr(fn, "_public")


def deprecated(fn: T_Callable) -> T_Callable:
    setattr(fn, "_deprecated", True)
    return fn


def is_deprecated(fn: Callable) -> bool:
    return hasattr(fn, "_deprecated") and getattr(fn, "_deprecated")
