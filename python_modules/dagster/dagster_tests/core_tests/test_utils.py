import time
from concurrent.futures import as_completed
from contextvars import ContextVar

import pytest
from dagster._core.test_utils import environ
from dagster._core.utils import InheritContextThreadPoolExecutor, parse_env_var
from dagster._utils.merger import merge_dicts


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


def test_merge():
    # two element merge
    assert merge_dicts({}, {}) == {}
    assert merge_dicts({1: 2}, {}) == {1: 2}
    assert merge_dicts({}, {1: 2}) == {1: 2}
    assert merge_dicts({1: 1}, {1: 2}) == {1: 2}

    # three element merge
    assert merge_dicts({}, {}, {}) == {}
    assert merge_dicts({1: 2}, {2: 3}, {3: 4}) == {1: 2, 2: 3, 3: 4}
    assert merge_dicts({1: 2}, {1: 3}, {1: 4}) == {1: 4}
