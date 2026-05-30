from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from dagster_shared.utils.cached_method import cached_method as cached_method

S = TypeVar("S")

CACHED_IF_TRUE_NO_ARG_METHOD_CACHE_FIELD = "_cached_if_true_no_arg_method_cache__internal__"


def cached_if_true_no_arg_method(method: Callable[[S], bool]) -> Callable[[S], bool]:
    """Caches the results of a zero-argument method call, only if it returns True.

    Usage:

        .. code-block:: python

            class MyClass:
                @cached_if_true_no_arg_method
                def col_c1_is_present_on_table_t1(self) -> bool:
                    ...

                @property
                @cached_if_true_no_arg_method
                def col_c2_is_present_on_table_t2(self) -> bool:
                    ...

            obj = MyClass()
            obj.col_c1_is_present_on_table_t1() # compute value, cache if True
            obj.col_c1_is_present_on_table_t1() # return cached True or re-compute value
            obj.col_c2_is_present_on_table_t2   # compute value, cache if True
            obj.col_c2_is_present_on_table_t2   # return cached True or re-compute value

    Intended for use when:
        - The method will be called frequently; AND
        - The method calls an external system such as a database; AND
        - If the result is ever True, there is an assumption that it will never return back to False
    """

    @wraps(method)
    def _cached_if_true_no_arg_method_wrapper(self: S) -> bool:
        if not hasattr(self, CACHED_IF_TRUE_NO_ARG_METHOD_CACHE_FIELD):
            setattr(self, CACHED_IF_TRUE_NO_ARG_METHOD_CACHE_FIELD, {})

        cache: dict[str, bool] = getattr(self, CACHED_IF_TRUE_NO_ARG_METHOD_CACHE_FIELD)
        method_name = method.__name__

        if method_name in cache:
            return cache[method_name]
        result = method(self)
        if result:
            cache[method_name] = result
        return result

    return _cached_if_true_no_arg_method_wrapper
