from pathlib import Path

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)

# ########################
# ##### ENVIRONMENT
# ########################


def test_set_env_succeeds():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("set", "env", "FOO=bar")
        assert_runner_result(result)
        assert Path(".env").read_text() == "FOO=bar"

        result = runner.invoke("set", "env", "FOO=baz")
        assert_runner_result(result)
        assert Path(".env").read_text() == "FOO=baz"

        result = runner.invoke("set", "env", "BAR=quux")
        assert_runner_result(result)

        result = runner.invoke("unset", "env", "FOO")
        assert_runner_result(result)
        assert Path(".env").read_text() == "BAR=quux"

        result = runner.invoke("unset", "env", "FOO")
        assert_runner_result(result, exit_0=False)
