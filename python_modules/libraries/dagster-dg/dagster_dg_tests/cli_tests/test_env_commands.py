import textwrap
from pathlib import Path

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)

# ########################
# ##### LIST
# ########################


def test_list_env_succeeds():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("env", "list")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            No environment variables are defined for this project.
        """).strip()
        )

        Path(".env").write_text("FOO=bar")
        result = runner.invoke("env", "list")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┓
               ┃ Env Var ┃ Value ┃
               ┡━━━━━━━━━╇━━━━━━━┩
               │ FOO     │ bar   │
               └─────────┴───────┘
        """).strip()
        )
