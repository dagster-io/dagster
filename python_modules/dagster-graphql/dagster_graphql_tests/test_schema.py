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
