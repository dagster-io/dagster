import shutil
import textwrap

from dagster_components.utils import format_error_message
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    fixed_panel_width,
    isolated_components_venv,
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    match_terminal_box_output,
)

# ########################
# ##### PROJECT
# ########################


def test_list_project_success():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        runner.invoke("scaffold", "project", "foo")
        runner.invoke("scaffold", "project", "bar")
        result = runner.invoke("list", "project")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
                bar
                foo
            """).strip()
        )


# ########################
# ##### COMPONENT
# ########################


def test_list_components_succeeds():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke("list", "component")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            qux
        """).strip()
        )


# ########################
# ##### COMPONENT TYPE
# ########################

_EXPECTED_COMPONENT_TYPES = textwrap.dedent("""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Component Type                                     ┃ Summary                                                         ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ dagster_test.components.AllMetadataEmptyComponent  │                                                                 │
    │ dagster_test.components.ComplexAssetComponent      │ An asset that has a complex schema.                             │
    │ dagster_test.components.SimpleAssetComponent       │ A simple asset that returns a constant string value.            │
    │ dagster_test.components.SimplePipesScriptComponent │ A simple asset that runs a Python script with the Pipes         │
    │                                                    │ subprocess client.                                              │
    └────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┘
""").strip()

_EXPECTED_COMPONENT_TYPES_JSON = textwrap.dedent("""
    [
        {
            "key": "dagster_test.components.AllMetadataEmptyComponent",
            "summary": null
        },
        {
            "key": "dagster_test.components.ComplexAssetComponent",
            "summary": "An asset that has a complex schema."
        },
        {
            "key": "dagster_test.components.SimpleAssetComponent",
            "summary": "A simple asset that returns a constant string value."
        },
        {
            "key": "dagster_test.components.SimplePipesScriptComponent",
            "summary": "A simple asset that runs a Python script with the Pipes subprocess client."
        }
    ]

""").strip()


def test_list_component_types_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke("list", "component-type")
            assert_runner_result(result)
            # strip the first line of logging output
            output = "\n".join(result.output.split("\n")[1:])
            match_terminal_box_output(output.strip(), _EXPECTED_COMPONENT_TYPES)


def test_list_component_type_json_succeeds():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("list", "component-type", "--json")
        assert_runner_result(result)
        # strip the first line of logging output
        output = "\n".join(result.output.split("\n")[1:])
        assert output.strip() == _EXPECTED_COMPONENT_TYPES_JSON


# Need to use capfd here to capture stderr from the subprocess invoked by the `list component-type`
# command. This subprocess inherits stderr from the parent process, for whatever reason `capsys` does
# not work.
def test_list_component_type_bad_entry_point_fails(capfd):
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        # Delete the component lib package referenced by the entry point
        shutil.rmtree("foo_bar/lib")

        # Disable cache to force re-discovery of deleted entry point
        result = runner.invoke("list", "component-type", "--disable-cache", "--json")
        assert_runner_result(result, exit_0=False)

        expected_error_message = format_error_message("""
            An error occurred while executing a `dagster-components` command in the
            Python environment
        """)
        assert expected_error_message in result.output

        captured = capfd.readouterr()
        assert "Error loading entry point `foo_bar` in group `dagster.components`." in captured.err
