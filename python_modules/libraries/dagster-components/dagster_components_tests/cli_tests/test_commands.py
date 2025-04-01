import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from dagster._core.test_utils import new_cwd
from dagster_components.cli import cli
from dagster_components.utils import ensure_dagster_components_tests_import
from dagster_shared import check
from dagster_shared.serdes.objects import (
    ComponentTypeSnap,
    LibraryObjectKey,
    LibraryObjectSnap,
    ScaffolderSnap,
)
from dagster_shared.serdes.serdes import deserialize_value
from jsonschema import Draft202012Validator, ValidationError

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import (
    assert_runner_result,
    create_project_from_components,
    temp_code_location_bar,
)


def test_list_library_objects_from_entry_points():
    runner = CliRunner()

    # First check the default behavior. We don't check the actual content because that may note be
    # stable (we are loading from all entry points).
    result = runner.invoke(cli, ["list", "library"])
    assert result.exit_code == 0
    result = json.loads(result.output)
    assert len(result) > 1


def test_list_library_objects_from_module():
    runner = CliRunner()
    # Now check what we get when we load directly from the test library. This has stable results.
    result = runner.invoke(cli, ["list", "library", "--no-entry-points", "dagster_test.components"])
    assert result.exit_code == 0
    result = check.is_list(deserialize_value(result.output), LibraryObjectSnap)
    assert len(result) > 1

    assert [obj.key.to_typename() for obj in result] == [
        "dagster_test.components.AllMetadataEmptyComponent",
        "dagster_test.components.ComplexAssetComponent",
        "dagster_test.components.SimpleAssetComponent",
        "dagster_test.components.SimplePipesScriptComponent",
    ]

    assert result[2] == ComponentTypeSnap(
        key=LibraryObjectKey(namespace="dagster_test.components", name="SimpleAssetComponent"),
        schema={
            "additionalProperties": False,
            "properties": {
                "asset_key": {"title": "Asset Key", "type": "string"},
                "value": {"title": "Value", "type": "string"},
            },
            "required": ["asset_key", "value"],
            "title": "SimpleAssetComponentModel",
            "type": "object",
        },
        description="A simple asset that returns a constant string value.",
        summary="A simple asset that returns a constant string value.",
        scaffolder=ScaffolderSnap(schema=None),
    )

    pipes_script_params_schema = {
        "properties": {
            "asset_key": {"title": "Asset Key", "type": "string"},
            "filename": {"title": "Filename", "type": "string"},
        },
        "required": ["asset_key", "filename"],
        "title": "SimplePipesScriptScaffoldParams",
        "type": "object",
    }

    assert result[3] == ComponentTypeSnap(
        key=LibraryObjectKey(
            namespace="dagster_test.components", name="SimplePipesScriptComponent"
        ),
        schema=pipes_script_params_schema,
        description="A simple asset that runs a Python script with the Pipes subprocess client.\n\nBecause it is a pipes asset, no value is returned.",
        summary="A simple asset that runs a Python script with the Pipes subprocess client.",
        scaffolder=ScaffolderSnap(schema=pipes_script_params_schema),
    )


def test_list_library_objects_from_project() -> None:
    """Tests that the list CLI picks components we add."""
    runner = CliRunner()

    # Now create a project and load the component types only from that project.
    with create_project_from_components(
        "definitions/local_component_sample",
        "definitions/other_local_component_sample",
        "definitions/single_file",
    ) as (tmpdir, location_name):
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                cli,
                [
                    "list",
                    "library",
                    "--no-entry-points",
                    f"{location_name}.defs.local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = deserialize_value(result.output, list)
            assert len(result) == 1
            assert result[0].key == LibraryObjectKey(
                namespace=f"{location_name}.defs.local_component_sample",
                name="MyComponent",
            )

            # Add a second module
            result = runner.invoke(
                cli,
                [
                    "list",
                    "library",
                    "--no-entry-points",
                    f"{location_name}.defs.local_component_sample",
                    f"{location_name}.defs.other_local_component_sample",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = deserialize_value(result.output, list)
            assert len(result) == 2
            assert [obj.key.to_typename() for obj in result] == [
                f"{location_name}.defs.local_component_sample.MyComponent",
                f"{location_name}.defs.other_local_component_sample.MyNewComponent",
            ]

            # Add another, non-local component directory, which no-ops
            result = runner.invoke(
                cli,
                [
                    "list",
                    "library",
                    "--no-entry-points",
                    f"{location_name}.defs.local_component_sample",
                    f"{location_name}.defs.other_local_component_sample",
                    f"{location_name}.defs.single_file",
                ],
            )

            assert result.exit_code == 0, str(result.stdout)

            result = deserialize_value(result.output, list)
            assert len(result) == 2


def test_all_components_schema_command():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "list",
            "all-components-schema",
            "--no-entry-points",
            "dagster_test.components",
        ],
    )
    assert_runner_result(result)
    result = json.loads(result.output)

    component_type_keys = [
        "ComplexAssetComponent",
        "SimpleAssetComponent",
        "SimplePipesScriptComponent",
    ]

    assert result["anyOf"] == [
        {"$ref": f"#/$defs/{component_type_key}"} for component_type_key in component_type_keys
    ]

    # Sanity check each of the component type schemas has a constant type property matching the
    # fully scoped component type key
    for component_type_key in component_type_keys:
        component_type_schema_def = result["$defs"][component_type_key]
        assert "type" in component_type_schema_def["properties"]
        assert (
            component_type_schema_def["properties"]["type"]["default"]
            == f"dagster_test.components.{component_type_key}"
        )
        assert (
            component_type_schema_def["properties"]["type"]["const"]
            == f"dagster_test.components.{component_type_key}"
        )
        assert "attributes" in component_type_schema_def["properties"]

    top_level_component_validator = Draft202012Validator(schema=result)
    top_level_component_validator.validate(
        {
            "type": "dagster_test.components.SimpleAssetComponent",
            "attributes": {"asset_key": "my_asset", "value": "my_value"},
        }
    )
    with pytest.raises(ValidationError):
        top_level_component_validator.validate(
            {
                "type": "dagster_test.components.SimpleAssetComponent",
                "attributes": {"asset_key": "my_asset", "value": "my_value"},
                "extra_key": "extra_value",
            }
        )


def test_scaffold_component_command():
    runner = CliRunner()

    with temp_code_location_bar():
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "object",
                "dagster_test.components.SimplePipesScriptComponent",
                "bar/components/qux",
                "--json-params",
                '{"asset_key": "my_asset", "filename": "my_asset.py"}',
                "--scaffold-format",
                "yaml",
            ],
        )
        assert_runner_result(result)
        assert Path("bar/components/qux/my_asset.py").exists()
