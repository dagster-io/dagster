from functools import wraps
from typing import AbstractSet, Callable, Dict, Hashable, Mapping, Tuple, Type, TypeVar

from typing_extensions import Concatenate, Final, ParamSpec

from dagster import _check as check

S = TypeVar("S")
T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable)
P = ParamSpec("P")


class _Sentinel:
    ...


NO_VALUE_IN_CACHE_SENTINEL: Final = _Sentinel()


def cached_method(method: Callable[Concatenate[S, P], T]) -> Callable[Concatenate[S, P], T]:
    """
    Caches the results of a method call.

    Usage:

        .. code-block:: python

            class MyClass:
                @cached_method
                def fetch_value_from_database(self, key):
                    ...

    The main difference between this decorator and `functools.lru_cache(max_size=None)` is that each
    instance of the class whose method is decorated gets its own cache. This means that the cache
    can be garbage-collected when the object is garbage-collected.

    A more subtle difference between this decorator and `functools.lru_cache` is that this one
    prioritizes preventing mistakes over ease-of-use and performance. With `functools.lru_cache`,
    these three invocations would all result in separate cache entries:

        .. code-block:: python

            class MyClass:
                @cached_method
                def a_method(self, arg1, arg2):
                    ...

            obj = MyClass()
            obj.a_method(arg1="a", arg2=5)
            obj.a_method(arg2=5, arg1="a")
            obj.a_method("a", 5)

    With this decorator, the first two would point to the same cache entry, and non-kwarg arguments
    are not allowed.
    """

    @wraps(method)
    def helper(self: S, *args: P.args, **kwargs: P.kwargs) -> T:
        cache_attr_name = method.__name__ + "_cache"
        if not hasattr(self, cache_attr_name):
            cache: Dict[Hashable, T] = {}
            setattr(self, cache_attr_name, cache)
        else:
            cache = getattr(self, cache_attr_name)

        key = _make_key(args, kwargs)
        cached_result = cache.get(key, NO_VALUE_IN_CACHE_SENTINEL)
        if not isinstance(cached_result, _Sentinel):
            return cached_result
        else:
            result = method(self, *args, **kwargs)
            cache[key] = result
            return result

    return helper


class _HashedSeq(list):
    """
    Adapted from https://github.com/python/cpython/blob/f9433fff476aa13af9cb314fcc6962055faa4085/Lib/functools.py#L432.

    This class guarantees that hash() will be called no more than once
    per element.  This is important because the lru_cache() will hash
    the key multiple times on a cache miss.
    """

    __slots__ = "hashvalue"

    def __init__(self, tup: Tuple[object, ...]):  # pylint: disable=super-init-not-called
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self) -> int:
        return self.hashvalue


def _make_key(
    args: Tuple[object, ...],
    kwds: Mapping[str, object],
    fasttypes: AbstractSet[Type[object]] = {int, str},
) -> Hashable:
    """
    Adapted from https://github.com/python/cpython/blob/f9433fff476aa13af9cb314fcc6962055faa4085/Lib/functools.py#L448.

    Make a cache key from optionally typed positional and keyword arguments
    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.
    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.
    """
    check.invariant(
        not args,
        (
            "@cached_method does not support non-keyword arguments, because doing so would enable "
            "functionally identical sets of arguments to correpond to different cache keys."
        ),
    )
    key = tuple()
    if kwds:
        key = tuple(sorted(kwds.items()))
    else:
        key = tuple()
    if len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)
