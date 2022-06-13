import json

import pytest
from click.testing import CliRunner
from dagster_graphql.cli import ui


@pytest.fixture(name="runner")
def runner_fixture():
    yield CliRunner()


def test_schema_type_names_without_graphene(runner):
    query = """
    query GetSchemaTypeNames {
        __schema {
            types {
                name
            }
        }
    }
    """

    result = runner.invoke(
        ui,
        ["--empty-workspace", "--ephemeral-instance", "-t", query],
    )
    graphql_schema_types = json.loads(result.output)["data"]["__schema"]["types"]

    violations = [
        graphql_type["name"]
        for graphql_type in graphql_schema_types
        if "Graphene".casefold() in graphql_type["name"].casefold()
    ]
    assert (
        not violations
    ), f"'Graphene' cannot be included in the GraphQL type name. Violating types: {violations}."


@pytest.mark.parametrize("operation_type", ["queryType", "mutationType"])
def test_schema_operation_fields_have_descriptions(runner, operation_type):
    query = f"""
    query GetOperationFieldDescriptions {{
        __schema {{
            {operation_type} {{
                name
                description
                fields {{
                    name
                    description
                }}
            }}
        }}
    }}
    """

    result = runner.invoke(
        ui,
        ["--empty-workspace", "--ephemeral-instance", "-t", query],
    )
    operation_type_root = json.loads(result.output)["data"]["__schema"][operation_type]

    assert operation_type_root[
        "description"
    ], f"Operation root '{operation_type_root['name']}' for '{operation_type}' must have a description."

    violations = [
        operation_field_type["name"]
        for operation_field_type in operation_type_root["fields"]
        if not operation_field_type["description"]
    ]
    assert (
        not violations
    ), f"Descriptions must be included in the GraphQL '{operation_type}' fields. Violating types: {violations}."
