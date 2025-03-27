import time
from concurrent.futures import as_completed
from contextvars import ContextVar
from typing import NamedTuple

import pytest
from dagster._core.test_utils import environ
from dagster._core.utils import InheritContextThreadPoolExecutor, parse_env_var
from dagster._utils import hash_collection


def test_parse_env_var_no_equals():
    env_var = "FOO_ENV_VAR"

    with pytest.raises(
        Exception, match="Tried to load environment variable FOO_ENV_VAR, but it was not set"
    ):
        parse_env_var(env_var)

    with environ({"FOO_ENV_VAR": "BAR_VALUE"}):
        assert parse_env_var(env_var) == ("FOO_ENV_VAR", "BAR_VALUE")


def test_parse_env_var_equals():
    env_var = "FOO_ENV_VAR=BAR_VALUE"
    assert parse_env_var(env_var) == ("FOO_ENV_VAR", "BAR_VALUE")


def test_parse_env_var_containing_equals():
    env_var = "FOO_ENV_VAR=HERE_COMES_THE_EQUALS=THERE_IT_WENT"

    assert parse_env_var(env_var) == ("FOO_ENV_VAR", "HERE_COMES_THE_EQUALS=THERE_IT_WENT")


def test_hash_collection():
    # lists have different hashes depending on order
    assert hash_collection([1, 2, 3]) == hash_collection([1, 2, 3])
    assert hash_collection([1, 2, 3]) != hash_collection([2, 1, 3])

    # dicts have same hash regardless of order
    assert hash_collection({"a": 1, "b": 2}) == hash_collection({"b": 2, "a": 1})

    assert hash_collection(set(range(10))) == hash_collection(set(range(10)))

    with pytest.raises(AssertionError):
        hash_collection(object())  # pyright: ignore[reportArgumentType]

    class Foo(NamedTuple):
        a: list[int]
        b: dict[str, int]
        c: str

    with pytest.raises(Exception):
        hash(Foo([1, 2, 3], {"a": 1}, "alpha"))

    class Bar(Foo):
        def __hash__(self):
            return hash_collection(self)

    assert hash(Bar([1, 2, 3], {"a": 1}, "alpha")) == hash(Bar([1, 2, 3], {"a": 1}, "alpha"))


def test_inherit_context_threadpool():
    id_cv = ContextVar("id")

    def in_thread(id_passed):
        assert id_passed == id_cv.get()
        return True

    with InheritContextThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        for i in range(10):
            id_cv.set(i)
            futures.append(executor.submit(in_thread, i))

        for f in as_completed(futures):
            assert f.result()


def test_inherit_context_threadpool_properties() -> None:
    def sleepy_thread():
        time.sleep(1)
        return True

    with InheritContextThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(10):
            futures.append(executor.submit(sleepy_thread))

        time.sleep(0.1)
        assert executor.max_workers == 5
        assert executor.num_running_futures == 5
        assert executor.num_queued_futures == 5

        for f in as_completed(futures):
            assert f.result()

        assert executor.num_running_futures == 0
        assert executor.num_queued_futures == 0

        # futures still have strong refs so are still tracked
        assert executor.weak_tracked_futures_count == 10

        futures = []
        f = None
        # now they dont
        assert executor.weak_tracked_futures_count == 0
