import json

import pytest
from click.testing import CliRunner
from dagster_graphql.cli import ui
from dagster_graphql.schema.pipelines.status import GrapheneRunStatus

GRAPHQL_TYPES_TO_ENFORCE_DESCRIPTION = {str(graphene_type) for graphene_type in [GrapheneRunStatus]}


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


def test_schema_types_have_descriptions(runner):
    """This test is opt-in right now, but once we have enough descriptions under test, we can
    switch this to be opt-out.
    """
    query = """
    query GetSchemaTypeDescriptions {
        __schema {
            types {
                name
                description
                enumValues {
                    name
                    description
                }
            }
        }
    }
    """

    result = runner.invoke(
        ui,
        ["--empty-workspace", "--ephemeral-instance", "-t", query],
    )
    graphql_schema_types = json.loads(result.output)["data"]["__schema"]["types"]

    filtered_graphql_schema_types = [
        graphql_type
        for graphql_type in graphql_schema_types
        if graphql_type["name"] in GRAPHQL_TYPES_TO_ENFORCE_DESCRIPTION
    ]

    violations = [
        graphql_type["name"]
        for graphql_type in filtered_graphql_schema_types
        if not graphql_type["description"]
    ]
    assert (
        not violations
    ), f"Descriptions must be included in the GraphQL types. Violating types: {violations}."

    enum_violations = [
        f"{graphql_type['name']}.{enum_value['name']}"
        for graphql_type in filtered_graphql_schema_types
        for enum_value in graphql_type.get("enumValues", [])
        if not enum_value["description"]
    ]
    assert not enum_violations, (
        "Descriptions must be included in the GraphQL enum values. Violating types:"
        f" {enum_violations}."
    )


@pytest.mark.parametrize("operation_type", ["queryType", "mutationType", "subscriptionType"])
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

    assert operation_type_root["description"], (
        f"Operation root '{operation_type_root['name']}' for '{operation_type}' must have a"
        " description."
    )

    violations = [
        operation_field_type["name"]
        for operation_field_type in operation_type_root["fields"]
        if not operation_field_type["description"]
    ]
    assert not violations, (
        f"Descriptions must be included in the GraphQL '{operation_type}' fields. Violating types:"
        f" {violations}."
    )
