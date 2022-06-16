import pytest

from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.core.utils import get_runs_iterator, make_new_run_id, parse_env_var


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


def test_get_runs_terator():
    with instance_for_test() as instance:
        assert list(get_runs_iterator(instance)) == []

        run_1 = create_run_for_test(instance, "foo", make_new_run_id())
        run_2 = create_run_for_test(instance, "foo", make_new_run_id())
        run_3 = create_run_for_test(instance, "foo", make_new_run_id())

        assert list(get_runs_iterator(instance)) == [run_3, run_2, run_1]

        instance.wipe()

        runs = []
        for i in range(50):
            runs.append(create_run_for_test(instance, "foo", make_new_run_id()))

        assert list(get_runs_iterator(instance, batch_size=7)) == list(reversed(runs))
