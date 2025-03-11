import inspect
import shutil
import textwrap
from pathlib import Path

import pytest
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
        result = runner.invoke("scaffold", "project", "foo")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "projects/bar")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "more_projects/baz")
        assert_runner_result(result)
        result = runner.invoke("list", "project")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
                foo
                projects/bar
                more_projects/baz
            """).strip()
        )


# ########################
# ##### COMPONENT
# ########################


def test_list_components_success():
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


def test_list_component_type_json_success():
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
        assert "Error loading entry point `foo_bar` in group `dagster_dg.library`." in captured.err


# ########################
# ##### DEFS
# ########################

_EXPECTED_DEFS = textwrap.dedent("""
    Assets
    ┏━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
    ┃ Key        ┃ Group   ┃ Deps ┃ Kinds ┃ Description ┃
    ┡━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
    │ my_asset_1 │ default │      │       │             │
    │ my_asset_2 │ default │      │       │             │
    └────────────┴─────────┴──────┴───────┴─────────────┘

    Jobs
    ┏━━━━━━━━━━━━━┓
    ┃ Name        ┃
    ┡━━━━━━━━━━━━━┩
    │ my_schedule │
    └─────────────┘

    Schedules
    ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
    ┃ Name        ┃ Cron schedule ┃
    ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
    │ my_schedule │ @daily        │
    └─────────────┴───────────────┘

    Sensors
    ┏━━━━━━━━━━━━━┓
    ┃ Name        ┃
    ┡━━━━━━━━━━━━━┩
    │ my_schedule │
    └─────────────┘
""").strip()

_EXPECTED_DEFS_JSON = textwrap.dedent("""
    [
        {
            "type": "asset",
            "key": "my_asset_1",
            "group": "default",
            "deps": [],
            "kinds": [],
            "description": null,
            "automation_condition": null
        },
        {
            "type": "asset",
            "key": "my_asset_2",
            "group": "default",
            "deps": [],
            "kinds": [],
            "description": null,
            "automation_condition": null
        },
        {
            "type": "job",
            "name": "my_job"
        },
        {
            "type": "schedule",
            "name": "my_schedule",
            "cron_schedule": "@daily"
        },
        {
            "type": "sensor",
            "name": "my_sensor"
        }
    ]
""").strip()


@pytest.mark.parametrize("use_json", [True, False])
def test_list_defs_succeeds(use_json: bool):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_components.dagster.DefinitionsComponent",
            "mydefs",
        )
        assert_runner_result(result)

        with Path("foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        if use_json:
            result = runner.invoke("list", "defs", "--json")
            assert_runner_result(result)
            output = "\n".join(result.output.split("\n")[1:])
            assert output.strip() == _EXPECTED_DEFS_JSON
        else:
            result = runner.invoke("list", "defs")
            assert_runner_result(result)
            output = "\n".join(result.output.split("\n")[1:])
            match_terminal_box_output(output.strip(), _EXPECTED_DEFS)


def _sample_defs():
    from dagster import asset, job, schedule, sensor

    @asset
    def my_asset_1(): ...

    @asset
    def my_asset_2(): ...

    @schedule(cron_schedule="@daily", target=[my_asset_1])
    def my_schedule(): ...

    @sensor(target=[my_asset_2])
    def my_sensor(): ...

    @job
    def my_job(): ...


_EXPECTED_COMPLEX_ASSET_DEFS = textwrap.dedent("""
    Assets
    ┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
    ┃ Key     ┃ Group   ┃ Deps  ┃ Kinds ┃ Description      ┃
    ┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
    │ alpha   │ group_1 │       │ sling │                  │
    │ beta    │ group_2 │       │ dbt   │ This is beta.    │
    │ delta   │ group_2 │ alpha │ dbt   │                  │
    │         │         │ beta  │       │                  │
    │ epsilon │ group_2 │ delta │ dbt   │ This is epsilon. │
    └─────────┴─────────┴───────┴───────┴──────────────────┘
""").strip()


def test_list_defs_complex_assets_succeeds():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke(
            "scaffold",
            "component",
            "dagster_components.dagster.DefinitionsComponent",
            "mydefs",
        )
        assert_runner_result(result)

        with Path("foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(
                inspect.getsource(_sample_complex_asset_defs).split("\n", 1)[1]
            )
            f.write(defs_source)

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = "\n".join(result.output.split("\n")[1:])
        match_terminal_box_output(output.strip(), _EXPECTED_COMPLEX_ASSET_DEFS)


def _sample_complex_asset_defs():
    from dagster import asset

    @asset(kinds={"sling"}, group_name="group_1")
    def alpha():
        pass

    @asset(
        kinds={"dbt"},
        group_name="group_2",
        description="This is beta.",
    )
    def beta():
        pass

    @asset(
        kinds={"dbt"},
        group_name="group_2",
    )
    def delta(alpha, beta):
        pass

    @asset(kinds={"dbt"}, group_name="group_2", description="This is epsilon.")
    def epsilon(delta):
        pass
